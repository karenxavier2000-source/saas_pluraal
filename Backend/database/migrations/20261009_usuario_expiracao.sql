ALTER TABLE pluraal.usuario
ADD COLUMN IF NOT EXISTS data_expiracao_login date;

COMMENT ON COLUMN pluraal.usuario.data_expiracao_login IS
'Último dia em que o usuário pode entrar e usar a plataforma; NULL significa acesso sem prazo.';
