-- Reference schema for the Text-to-SQL & Document Chat Platform application database.
-- Generated from the Alembic migrations (backend/migrations/versions/) - this file is for
-- reading/reference only. To actually set up the database, run `alembic upgrade head`
-- (the Docker Compose setup does this automatically). Do not run this file by hand against
-- a database that already has Alembic-managed tables.



CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);

CREATE TABLE public.audit_logs (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    user_id uuid,
    action character varying(100) NOT NULL,
    resource_type character varying(100),
    resource_id character varying(100),
    ip_address character varying(64),
    details jsonb NOT NULL,
    status character varying(30) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.column_permissions (
    id uuid NOT NULL,
    table_permission_id uuid NOT NULL,
    column_id uuid NOT NULL,
    can_read boolean NOT NULL,
    can_filter boolean NOT NULL,
    mask_type character varying(50)
);

CREATE TABLE public.conversations (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    user_id uuid NOT NULL,
    title character varying(500),
    status character varying(30) NOT NULL,
    active_connection_ids jsonb NOT NULL,
    active_knowledge_base_ids jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_message_at timestamp with time zone
);

CREATE TABLE public.database_columns (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    table_id uuid NOT NULL,
    column_name character varying(255) NOT NULL,
    data_type character varying(100) NOT NULL,
    ordinal_position integer,
    is_nullable boolean,
    is_primary_key boolean NOT NULL,
    is_foreign_key boolean NOT NULL,
    is_sensitive boolean NOT NULL,
    referenced_table character varying(255),
    referenced_column character varying(255),
    sample_values jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.database_connections (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    created_by uuid,
    name character varying(200) NOT NULL,
    database_type character varying(50) NOT NULL,
    host character varying(255),
    port integer,
    database_name character varying(255),
    username character varying(255),
    encrypted_password text,
    ssl_enabled boolean NOT NULL,
    connection_options jsonb NOT NULL,
    status character varying(30) NOT NULL,
    last_tested_at timestamp with time zone,
    last_test_message text,
    schema_sync_status character varying(30) NOT NULL,
    last_schema_sync_at timestamp with time zone,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.database_tables (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    connection_id uuid NOT NULL,
    schema_name character varying(255) NOT NULL,
    table_name character varying(255) NOT NULL,
    table_type character varying(50) NOT NULL,
    description text,
    estimated_row_count bigint,
    primary_key_columns jsonb NOT NULL,
    is_enabled boolean NOT NULL,
    is_sensitive boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.document_chunks (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid NOT NULL,
    file_id uuid NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    page_number integer,
    section_title character varying(500),
    token_count integer,
    metadata jsonb NOT NULL,
    embedding public.vector(384),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.files (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    knowledge_base_id uuid,
    uploaded_by uuid,
    original_name character varying(500) NOT NULL,
    stored_name character varying(500) NOT NULL,
    storage_path text NOT NULL,
    mime_type character varying(255),
    extension character varying(30),
    file_size_bytes bigint,
    checksum character varying(128),
    processing_status character varying(30) NOT NULL,
    processing_error text,
    page_count integer,
    extracted_text_length bigint,
    metadata jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    processed_at timestamp with time zone
);

CREATE TABLE public.knowledge_bases (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    created_by uuid,
    name character varying(200) NOT NULL,
    description text,
    embedding_model character varying(255),
    chunking_config jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.message_citations (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    message_id uuid NOT NULL,
    citation_type character varying(30) NOT NULL,
    file_id uuid,
    chunk_id uuid,
    query_execution_id uuid,
    title text,
    source_reference text,
    page_number integer,
    relevance_score numeric(8,6),
    metadata jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.messages (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    role character varying(30) NOT NULL,
    content text NOT NULL,
    detected_intent character varying(50),
    selected_sources jsonb NOT NULL,
    model_name character varying(255),
    latency_ms integer,
    status character varying(30) NOT NULL,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.query_executions (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    conversation_id uuid,
    message_id uuid,
    connection_id uuid NOT NULL,
    generated_sql text NOT NULL,
    normalized_sql text,
    validation_status character varying(30) NOT NULL,
    validation_errors jsonb NOT NULL,
    applied_row_filters jsonb NOT NULL,
    referenced_tables jsonb NOT NULL,
    execution_status character varying(30),
    execution_time_ms integer,
    returned_row_count integer,
    result_preview jsonb,
    error_code character varying(100),
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.roles (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.table_permissions (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    role_id uuid,
    user_id uuid,
    connection_id uuid NOT NULL,
    table_id uuid NOT NULL,
    can_read boolean NOT NULL,
    can_insert boolean NOT NULL,
    can_update boolean NOT NULL,
    can_delete boolean NOT NULL,
    row_filter jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_permission_subject CHECK ((((role_id IS NOT NULL) AND (user_id IS NULL)) OR ((role_id IS NULL) AND (user_id IS NOT NULL))))
);

CREATE TABLE public.tenants (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    code character varying(100) NOT NULL,
    status character varying(30) NOT NULL,
    settings jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.user_roles (
    user_id uuid NOT NULL,
    role_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.users (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255),
    password_hash character varying NOT NULL,
    status character varying(30) NOT NULL,
    is_tenant_admin boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.column_permissions
    ADD CONSTRAINT column_permissions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.database_columns
    ADD CONSTRAINT database_columns_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.database_connections
    ADD CONSTRAINT database_connections_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.database_tables
    ADD CONSTRAINT database_tables_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.knowledge_bases
    ADD CONSTRAINT knowledge_bases_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.message_citations
    ADD CONSTRAINT message_citations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.query_executions
    ADD CONSTRAINT query_executions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.table_permissions
    ADD CONSTRAINT table_permissions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_code_key UNIQUE (code);

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.column_permissions
    ADD CONSTRAINT uq_column_permission UNIQUE (table_permission_id, column_id);

ALTER TABLE ONLY public.database_columns
    ADD CONSTRAINT uq_database_column UNIQUE (table_id, column_name);

ALTER TABLE ONLY public.database_connections
    ADD CONSTRAINT uq_database_connection_name UNIQUE (tenant_id, name);

ALTER TABLE ONLY public.database_tables
    ADD CONSTRAINT uq_database_table UNIQUE (connection_id, schema_name, table_name);

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT uq_document_chunk UNIQUE (file_id, chunk_index);

ALTER TABLE ONLY public.knowledge_bases
    ADD CONSTRAINT uq_knowledge_base_name UNIQUE (tenant_id, name);

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT uq_roles_tenant_name UNIQUE (tenant_id, name);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_tenant_email UNIQUE (tenant_id, email);

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

CREATE INDEX ix_audit_logs_tenant_id ON public.audit_logs USING btree (tenant_id);

CREATE INDEX ix_conversations_tenant_id ON public.conversations USING btree (tenant_id);

CREATE INDEX ix_conversations_user_id ON public.conversations USING btree (user_id);

CREATE INDEX ix_database_columns_table_id ON public.database_columns USING btree (table_id);

CREATE INDEX ix_database_columns_tenant_id ON public.database_columns USING btree (tenant_id);

CREATE INDEX ix_database_connections_tenant_id ON public.database_connections USING btree (tenant_id);

CREATE INDEX ix_database_tables_connection_id ON public.database_tables USING btree (connection_id);

CREATE INDEX ix_database_tables_tenant_id ON public.database_tables USING btree (tenant_id);

CREATE INDEX ix_document_chunks_file_id ON public.document_chunks USING btree (file_id);

CREATE INDEX ix_document_chunks_knowledge_base_id ON public.document_chunks USING btree (knowledge_base_id);

CREATE INDEX ix_document_chunks_tenant_id ON public.document_chunks USING btree (tenant_id);

CREATE INDEX ix_files_knowledge_base_id ON public.files USING btree (knowledge_base_id);

CREATE INDEX ix_files_tenant_id ON public.files USING btree (tenant_id);

CREATE INDEX ix_knowledge_bases_tenant_id ON public.knowledge_bases USING btree (tenant_id);

CREATE INDEX ix_message_citations_message_id ON public.message_citations USING btree (message_id);

CREATE INDEX ix_message_citations_tenant_id ON public.message_citations USING btree (tenant_id);

CREATE INDEX ix_messages_conversation_id ON public.messages USING btree (conversation_id);

CREATE INDEX ix_messages_tenant_id ON public.messages USING btree (tenant_id);

CREATE INDEX ix_query_executions_tenant_id ON public.query_executions USING btree (tenant_id);

CREATE INDEX ix_roles_tenant_id ON public.roles USING btree (tenant_id);

CREATE INDEX ix_table_permissions_tenant_id ON public.table_permissions USING btree (tenant_id);

CREATE INDEX ix_users_tenant_id ON public.users USING btree (tenant_id);

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.column_permissions
    ADD CONSTRAINT column_permissions_column_id_fkey FOREIGN KEY (column_id) REFERENCES public.database_columns(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.column_permissions
    ADD CONSTRAINT column_permissions_table_permission_id_fkey FOREIGN KEY (table_permission_id) REFERENCES public.table_permissions(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.database_columns
    ADD CONSTRAINT database_columns_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.database_tables(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.database_columns
    ADD CONSTRAINT database_columns_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.database_connections
    ADD CONSTRAINT database_connections_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.database_connections
    ADD CONSTRAINT database_connections_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.database_tables
    ADD CONSTRAINT database_tables_connection_id_fkey FOREIGN KEY (connection_id) REFERENCES public.database_connections(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.database_tables
    ADD CONSTRAINT database_tables_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.files(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_knowledge_base_id_fkey FOREIGN KEY (knowledge_base_id) REFERENCES public.knowledge_bases(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_knowledge_base_id_fkey FOREIGN KEY (knowledge_base_id) REFERENCES public.knowledge_bases(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.knowledge_bases
    ADD CONSTRAINT knowledge_bases_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.knowledge_bases
    ADD CONSTRAINT knowledge_bases_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.message_citations
    ADD CONSTRAINT message_citations_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.document_chunks(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.message_citations
    ADD CONSTRAINT message_citations_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.files(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.message_citations
    ADD CONSTRAINT message_citations_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.messages(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.message_citations
    ADD CONSTRAINT message_citations_query_execution_id_fkey FOREIGN KEY (query_execution_id) REFERENCES public.query_executions(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.message_citations
    ADD CONSTRAINT message_citations_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.query_executions
    ADD CONSTRAINT query_executions_connection_id_fkey FOREIGN KEY (connection_id) REFERENCES public.database_connections(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.query_executions
    ADD CONSTRAINT query_executions_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.query_executions
    ADD CONSTRAINT query_executions_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.messages(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.query_executions
    ADD CONSTRAINT query_executions_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.table_permissions
    ADD CONSTRAINT table_permissions_connection_id_fkey FOREIGN KEY (connection_id) REFERENCES public.database_connections(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.table_permissions
    ADD CONSTRAINT table_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.table_permissions
    ADD CONSTRAINT table_permissions_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.database_tables(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.table_permissions
    ADD CONSTRAINT table_permissions_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.table_permissions
    ADD CONSTRAINT table_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


