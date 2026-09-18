CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL,
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (version)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;
