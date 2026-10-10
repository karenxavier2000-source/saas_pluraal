import unittest
import json
import psycopg
from Backend.server import create_app
from Backend.config.settings import settings
from Backend.services.security_service import hash_password, create_access_token

class TestDelegationAndSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Database connection for test setup and teardown
        cls.conn = psycopg.connect(
            host=settings.PGHOST,
            port=settings.PGPORT,
            dbname=settings.PGDATABASE,
            user=settings.PGUSER,
            password=settings.PGPASSWORD,
            autocommit=True
        )
        cls.cur = cls.conn.cursor()

        # Pick known entities from escolas_pluraal
        cls.cur.execute("""
            SELECT "SIGLA_UNIAO", "SIGLA_ASSOCIACAO", id_escolas
            FROM pluraal.escolas_pluraal
            WHERE "SIGLA_UNIAO" IS NOT NULL AND "SIGLA_ASSOCIACAO" IS NOT NULL
            ORDER BY id_escolas LIMIT 20;
        """)
        cls.sample_schools = cls.cur.fetchall()
        # Find two different unioes
        cls.cur.execute('SELECT DISTINCT "SIGLA_UNIAO" FROM pluraal.escolas_pluraal WHERE "SIGLA_UNIAO" IS NOT NULL LIMIT 2;')
        cls.sample_unioes = [r[0] for r in cls.cur.fetchall()]
        cls.uniao_a = cls.sample_unioes[0]
        cls.uniao_b = cls.sample_unioes[1] if len(cls.sample_unioes) > 1 else "OTHER_UNIAO"

        # Find associations for uniao_a
        cls.cur.execute('SELECT DISTINCT "SIGLA_ASSOCIACAO" FROM pluraal.escolas_pluraal WHERE "SIGLA_UNIAO" = %s LIMIT 2;', (cls.uniao_a,))
        cls.sample_assocs_a = [r[0] for r in cls.cur.fetchall()]
        cls.assoc_a1 = cls.sample_assocs_a[0]
        cls.assoc_a2 = cls.sample_assocs_a[1] if len(cls.sample_assocs_a) > 1 else cls.assoc_a1

        # Find schools for assoc_a1
        cls.cur.execute('SELECT id_escolas FROM pluraal.escolas_pluraal WHERE "SIGLA_UNIAO" = %s AND "SIGLA_ASSOCIACAO" = %s LIMIT 3;', (cls.uniao_a, cls.assoc_a1))
        cls.sample_escolas_a1 = [r[0] for r in cls.cur.fetchall()]
        cls.escola_1 = cls.sample_escolas_a1[0]
        cls.escola_2 = cls.sample_escolas_a1[1] if len(cls.sample_escolas_a1) > 1 else cls.escola_1

        # Schools for uniao_b
        cls.cur.execute('SELECT id_escolas, "SIGLA_ASSOCIACAO" FROM pluraal.escolas_pluraal WHERE "SIGLA_UNIAO" = %s LIMIT 1;', (cls.uniao_b,))
        r_b = cls.cur.fetchone()
        cls.escola_b = r_b[0] if r_b else None
        cls.assoc_b = r_b[1] if r_b else None

    @classmethod
    def tearDownClass(cls):
        # Clean up any test users created
        cls.cur.execute("DELETE FROM pluraal.usuario_acesso WHERE id_usuario IN (SELECT id_usuario FROM pluraal.usuario WHERE email LIKE 'test_%@test.com');")
        cls.cur.execute("DELETE FROM pluraal.usuario WHERE email LIKE 'test_%@test.com';")
        cls.cur.close()
        cls.conn.close()

    def create_db_user(self, nome, email, hierarquia, ativo=True, trocar_senha=False, pode_criar=False, criado_por=1, accesses=None):
        pw_hash = hash_password("Test@1234")
        self.cur.execute("""
            INSERT INTO pluraal.usuario (
                nome_completo_usuario, email, senha, hierarquia,
                ativo, trocar_senha_no_primeiro_acesso, pode_criar_usuario,
                criado_por_usuario_id, token_versao
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
            RETURNING id_usuario;
        """, (nome, email.lower(), pw_hash, hierarquia, ativo, trocar_senha, pode_criar, criado_por))
        uid = self.cur.fetchone()[0]

        if accesses:
            for acc in accesses:
                self.cur.execute("""
                    INSERT INTO pluraal.usuario_acesso (
                        id_usuario, tipo, sigla_uniao, sigla_associacao, id_escolas
                    ) VALUES (%s, %s, %s, %s, %s);
                """, (uid, acc.get("tipo"), acc.get("sigla_uniao"), acc.get("sigla_associacao"), acc.get("id_escolas")))

        token = create_access_token({
            "id_usuario": uid,
            "email": email.lower(),
            "nome_completo_usuario": nome,
            "hierarquia": hierarquia,
            "trocar_senha_no_primeiro_acesso": trocar_senha,
            "pode_criar_usuario": pode_criar,
            "token_versao": 1
        })
        return uid, token

    def test_01_inactive_user_cannot_login(self):
        uid, _ = self.create_db_user("Inactive User", "test_inactive@test.com", "escola", ativo=False)
        res = self.client.post("/api/auth/login", json={"email": "test_inactive@test.com", "senha": "Test@1234"})
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertEqual(data["error"], "USER_INACTIVE")

    def test_02_mandatory_password_change_blocks_protected_api(self):
        uid, token = self.create_db_user("First Access User", "test_firstaccess@test.com", "escola", trocar_senha=True)
        # Try to access protected endpoint /api/users
        res = self.client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertEqual(data["error"], "FORCE_PASSWORD_CHANGE")

    def test_03_change_password_unlocks_access_and_invalidates_old_token(self):
        uid, old_token = self.create_db_user("Password Changer", "test_pwchange@test.com", "Master", trocar_senha=True)
        # Change password
        res = self.client.post("/api/auth/change-password", headers={"Authorization": f"Bearer {old_token}"}, json={
            "senha_atual": "Test@1234",
            "nova_senha": "NewSecretPass@2026",
            "confirmacao_senha": "NewSecretPass@2026"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        new_token = data["token"]

        # Old token must now be rejected because token_versao changed!
        res_old = self.client.get("/api/users", headers={"Authorization": f"Bearer {old_token}"})
        self.assertEqual(res_old.status_code, 401)
        self.assertEqual(res_old.get_json()["error"], "SESSION_REVOKED")

        # New token must succeed
        res_new = self.client.get("/api/users", headers={"Authorization": f"Bearer {new_token}"})
        self.assertEqual(res_new.status_code, 200)

    def test_04_user_without_pode_criar_usuario_cannot_create_users(self):
        uid, token = self.create_db_user("No Perm Creator", "test_noperm@test.com", "uniao", pode_criar=False, accesses=[
            {"tipo": "uniao", "sigla_uniao": self.uniao_a}
        ])
        res = self.client.post("/api/users", headers={"Authorization": f"Bearer {token}"}, json={
            "nome_completo_usuario": "Sub User",
            "email": "test_sub1@test.com",
            "hierarquia": "escola",
            "acessos": [{"tipo": "escola", "id_escolas": self.escola_1}]
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("pode_criar_usuario = false", res.get_json()["message"])

    def test_05_non_master_cannot_create_master_user(self):
        uid, token = self.create_db_user("Uniao Creator", "test_uniao_createmaster@test.com", "uniao", pode_criar=True, accesses=[
            {"tipo": "uniao", "sigla_uniao": self.uniao_a}
        ])
        res = self.client.post("/api/users", headers={"Authorization": f"Bearer {token}"}, json={
            "nome_completo_usuario": "Fake Master",
            "email": "test_fakemaster@test.com",
            "hierarquia": "Master"
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("Apenas usuários Master podem criar ou gerenciar usuários com hierarquia Master", res.get_json()["message"])

    def test_06_non_master_cannot_grant_pode_criar_usuario(self):
        uid, token = self.create_db_user("Uniao Creator 2", "test_uniao_grantperm@test.com", "uniao", pode_criar=True, accesses=[
            {"tipo": "uniao", "sigla_uniao": self.uniao_a}
        ])
        res = self.client.post("/api/users", headers={"Authorization": f"Bearer {token}"}, json={
            "nome_completo_usuario": "Sub With Perm",
            "email": "test_subwithperm@test.com",
            "hierarquia": "associacao",
            "pode_criar_usuario": True,
            "acessos": [{"tipo": "associacao", "sigla_uniao": self.uniao_a, "sigla_associacao": self.assoc_a1}]
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("Somente o Master pode conceder a permissão de criar usuários", res.get_json()["message"])

    def test_07_non_master_cannot_alter_own_hierarchy_or_accesses(self):
        uid, token = self.create_db_user("Uniao Self Edit", "test_selfedit@test.com", "uniao", pode_criar=True, accesses=[
            {"tipo": "uniao", "sigla_uniao": self.uniao_a}
        ])
        # Try to upgrade self to Master
        res = self.client.put(f"/api/users/{uid}", headers={"Authorization": f"Bearer {token}"}, json={
            "nome_completo_usuario": "Uniao Self Edit Promoted",
            "email": "test_selfedit@test.com",
            "hierarquia": "Master"
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("Você não tem permissão para alterar sua própria hierarquia", res.get_json()["message"])

    def test_08_uniao_creator_cannot_grant_outside_their_uniao(self):
        uid, token = self.create_db_user("Uniao Creator Restricted", "test_uniao_bounds@test.com", "uniao", pode_criar=True, accesses=[
            {"tipo": "uniao", "sigla_uniao": self.uniao_a}
        ])
        # Try to grant uniao_b
        res = self.client.post("/api/users", headers={"Authorization": f"Bearer {token}"}, json={
            "nome_completo_usuario": "Trespasser User",
            "email": "test_trespasser1@test.com",
            "hierarquia": "uniao",
            "acessos": [{"tipo": "uniao", "sigla_uniao": self.uniao_b}]
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("fora do escopo do criador", res.get_json()["message"])

    def test_09_associacao_creator_cannot_create_uniao_or_grant_outside_assoc(self):
        uid, token = self.create_db_user("Assoc Creator", "test_assoc_bounds@test.com", "associacao", pode_criar=True, accesses=[
            {"tipo": "associacao", "sigla_uniao": self.uniao_a, "sigla_associacao": self.assoc_a1}
        ])
        # 1. Cannot create uniao user
        res1 = self.client.post("/api/users", headers={"Authorization": f"Bearer {token}"}, json={
            "nome_completo_usuario": "Attempt Uniao",
            "email": "test_attemptuniao@test.com",
            "hierarquia": "uniao",
            "acessos": [{"tipo": "uniao", "sigla_uniao": self.uniao_a}]
        })
        self.assertEqual(res1.status_code, 403)
        self.assertIn("não pode criar ou definir usuários com hierarquia 'uniao'", res1.get_json()["message"])

        # 2. Cannot grant school from another association
        if self.escola_b:
            res2 = self.client.post("/api/users", headers={"Authorization": f"Bearer {token}"}, json={
                "nome_completo_usuario": "School Trespasser",
                "email": "test_trespasser2@test.com",
                "hierarquia": "escola",
                "acessos": [{"tipo": "escola", "id_escolas": self.escola_b}]
            })
            self.assertEqual(res2.status_code, 403)
            self.assertIn("fora do escopo do criador", res2.get_json()["message"])

    def test_10_escola_creator_can_only_create_escola_within_own_escolas(self):
        uid, token = self.create_db_user("Escola Creator", "test_escola_creator@test.com", "escola", pode_criar=True, accesses=[
            {"tipo": "escola", "id_escolas": self.escola_1}
        ])
        # 1. Cannot create associacao
        res1 = self.client.post("/api/users", headers={"Authorization": f"Bearer {token}"}, json={
            "nome_completo_usuario": "Attempt Assoc",
            "email": "test_attemptassoc@test.com",
            "hierarquia": "associacao",
            "acessos": [{"tipo": "associacao", "sigla_uniao": self.uniao_a, "sigla_associacao": self.assoc_a1}]
        })
        self.assertEqual(res1.status_code, 403)

        # 2. Cannot grant another school
        if self.escola_2 and self.escola_2 != self.escola_1:
            res2 = self.client.post("/api/users", headers={"Authorization": f"Bearer {token}"}, json={
                "nome_completo_usuario": "Sub Escola Invalid",
                "email": "test_subescolainvalid@test.com",
                "hierarquia": "escola",
                "acessos": [{"tipo": "escola", "id_escolas": self.escola_2}]
            })
            self.assertEqual(res2.status_code, 403)
            self.assertIn("fora do escopo do criador", res2.get_json()["message"])

    def test_11_reducing_creator_access_blocked_when_child_would_exceed_boundary(self):
        # 1. Master creates Creator User with 2 schools
        _, master_token = self.create_db_user("Master Tester", "test_master_reduce@test.com", "Master", pode_criar=True)
        creator_id, _ = self.create_db_user("Parent Creator", "test_parent_creator@test.com", "escola", pode_criar=True, accesses=[
            {"tipo": "escola", "id_escolas": self.escola_1},
            {"tipo": "escola", "id_escolas": self.escola_2}
        ])

        # 2. Creator creates Subordinate User with escola_2
        sub_id, _ = self.create_db_user("Child Sub", "test_child_sub@test.com", "escola", pode_criar=False, criado_por=creator_id, accesses=[
            {"tipo": "escola", "id_escolas": self.escola_2}
        ])

        # 3. Master attempts to reduce Creator's access to ONLY escola_1 (removing escola_2)
        res = self.client.put(f"/api/users/{creator_id}", headers={"Authorization": f"Bearer {master_token}"}, json={
            "nome_completo_usuario": "Parent Creator Reduced",
            "email": "test_parent_creator@test.com",
            "hierarquia": "escola",
            "acessos": [{"tipo": "escola", "id_escolas": self.escola_1}]
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data["error"], "DELEGATION_REDUCTION_CONFLICT")
        self.assertTrue(len(data["conflitos"]) > 0)
        self.assertEqual(data["conflitos"][0]["id_usuario"], sub_id)

    def test_12_password_reset_by_admin_invalidates_current_session(self):
        # Create user
        uid, token = self.create_db_user("Reset Target", "test_reset_target@test.com", "escola")
        _, master_token = self.create_db_user("Admin User", "test_admin_reset@test.com", "Master")

        # Admin resets password
        res = self.client.post(f"/api/users/{uid}/reset-password", headers={"Authorization": f"Bearer {master_token}"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("senha_temporaria", data)
        temp_pw = data["senha_temporaria"]

        # Target user's existing token must now be invalid!
        res_check = self.client.get(f"/api/users/{uid}", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_check.status_code, 401)
        self.assertEqual(res_check.get_json()["error"], "SESSION_REVOKED")

        # Target user can now login with temporary password and must be forced to change
        res_login = self.client.post("/api/auth/login", json={"email": "test_reset_target@test.com", "senha": temp_pw})
        self.assertEqual(res_login.status_code, 200)
        login_data = res_login.get_json()
        self.assertTrue(login_data["usuario"]["trocar_senha_no_primeiro_acesso"])

if __name__ == "__main__":
    unittest.main()
