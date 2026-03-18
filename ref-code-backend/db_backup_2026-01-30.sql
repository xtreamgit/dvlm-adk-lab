--
-- PostgreSQL database dump
--

\restrict QM478XTflUizLGdE70WWmQi5cof9C8NAbWDvxCxfwgx175u29gDFKy9nwE9o7ir

-- Dumped from database version 15.15 (Debian 15.15-1.pgdg13+1)
-- Dumped by pg_dump version 15.15 (Debian 15.15-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agents; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.agents (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    instructions text,
    model character varying(255) DEFAULT 'gemini-2.0-flash-exp'::character varying,
    temperature double precision DEFAULT 0.7,
    top_p double precision DEFAULT 0.95,
    top_k integer DEFAULT 40,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    display_name character varying(255) NOT NULL,
    config_path character varying(255) NOT NULL
);


ALTER TABLE public.agents OWNER TO adk_dev_user;

--
-- Name: agents_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.agents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.agents_id_seq OWNER TO adk_dev_user;

--
-- Name: agents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.agents_id_seq OWNED BY public.agents.id;


--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.chat_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    agent_id integer,
    title character varying(255),
    message_count integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.chat_sessions OWNER TO adk_dev_user;

--
-- Name: chat_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.chat_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.chat_sessions_id_seq OWNER TO adk_dev_user;

--
-- Name: chat_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.chat_sessions_id_seq OWNED BY public.chat_sessions.id;


--
-- Name: corpora; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.corpora (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    description text,
    gcs_bucket character varying(255),
    vertex_corpus_id character varying(255),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.corpora OWNER TO adk_dev_user;

--
-- Name: corpora_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.corpora_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.corpora_id_seq OWNER TO adk_dev_user;

--
-- Name: corpora_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.corpora_id_seq OWNED BY public.corpora.id;


--
-- Name: corpus_audit_log; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.corpus_audit_log (
    id integer NOT NULL,
    corpus_id integer,
    user_id integer,
    action character varying(100) NOT NULL,
    changes text,
    metadata text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.corpus_audit_log OWNER TO adk_dev_user;

--
-- Name: corpus_audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.corpus_audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.corpus_audit_log_id_seq OWNER TO adk_dev_user;

--
-- Name: corpus_audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.corpus_audit_log_id_seq OWNED BY public.corpus_audit_log.id;


--
-- Name: corpus_metadata; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.corpus_metadata (
    id integer NOT NULL,
    corpus_id integer NOT NULL,
    created_by integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_synced_at timestamp without time zone,
    last_synced_by integer,
    sync_status character varying(50) DEFAULT 'active'::character varying,
    sync_error_message text,
    document_count integer DEFAULT 0,
    last_document_count_update timestamp without time zone,
    tags text,
    notes text
);


ALTER TABLE public.corpus_metadata OWNER TO adk_dev_user;

--
-- Name: corpus_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.corpus_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.corpus_metadata_id_seq OWNER TO adk_dev_user;

--
-- Name: corpus_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.corpus_metadata_id_seq OWNED BY public.corpus_metadata.id;


--
-- Name: document_access_log; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.document_access_log (
    id integer NOT NULL,
    user_id integer NOT NULL,
    corpus_id integer NOT NULL,
    document_name character varying(255) NOT NULL,
    document_file_id character varying(255),
    access_type character varying(50) DEFAULT 'view'::character varying,
    success boolean NOT NULL,
    error_message text,
    source_uri text,
    ip_address character varying(45),
    user_agent text,
    accessed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.document_access_log OWNER TO adk_dev_user;

--
-- Name: TABLE document_access_log; Type: COMMENT; Schema: public; Owner: adk_dev_user
--

COMMENT ON TABLE public.document_access_log IS 'Audit trail for all document retrieval and access attempts';


--
-- Name: COLUMN document_access_log.access_type; Type: COMMENT; Schema: public; Owner: adk_dev_user
--

COMMENT ON COLUMN public.document_access_log.access_type IS 'Type of access: view, download, preview';


--
-- Name: COLUMN document_access_log.success; Type: COMMENT; Schema: public; Owner: adk_dev_user
--

COMMENT ON COLUMN public.document_access_log.success IS 'Whether the access attempt was successful';


--
-- Name: COLUMN document_access_log.error_message; Type: COMMENT; Schema: public; Owner: adk_dev_user
--

COMMENT ON COLUMN public.document_access_log.error_message IS 'Error message if access failed';


--
-- Name: document_access_log_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.document_access_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.document_access_log_id_seq OWNER TO adk_dev_user;

--
-- Name: document_access_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.document_access_log_id_seq OWNED BY public.document_access_log.id;


--
-- Name: group_corpora; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.group_corpora (
    group_id integer NOT NULL,
    corpus_id integer NOT NULL
);


ALTER TABLE public.group_corpora OWNER TO adk_dev_user;

--
-- Name: group_corpus_access; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.group_corpus_access (
    id integer NOT NULL,
    group_id integer NOT NULL,
    corpus_id integer NOT NULL,
    permission character varying(20) DEFAULT 'read'::character varying,
    granted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.group_corpus_access OWNER TO adk_dev_user;

--
-- Name: group_corpus_access_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.group_corpus_access_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.group_corpus_access_id_seq OWNER TO adk_dev_user;

--
-- Name: group_corpus_access_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.group_corpus_access_id_seq OWNED BY public.group_corpus_access.id;


--
-- Name: group_roles; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.group_roles (
    group_id integer NOT NULL,
    role_id integer NOT NULL
);


ALTER TABLE public.group_roles OWNER TO adk_dev_user;

--
-- Name: groups; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.groups (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.groups OWNER TO adk_dev_user;

--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.groups_id_seq OWNER TO adk_dev_user;

--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.groups_id_seq OWNED BY public.groups.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    permissions jsonb DEFAULT '[]'::jsonb
);


ALTER TABLE public.roles OWNER TO adk_dev_user;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_id_seq OWNER TO adk_dev_user;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: session_corpus_selections; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.session_corpus_selections (
    id integer NOT NULL,
    user_id integer NOT NULL,
    corpus_id integer NOT NULL,
    last_selected_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.session_corpus_selections OWNER TO adk_dev_user;

--
-- Name: session_corpus_selections_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.session_corpus_selections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.session_corpus_selections_id_seq OWNER TO adk_dev_user;

--
-- Name: session_corpus_selections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.session_corpus_selections_id_seq OWNED BY public.session_corpus_selections.id;


--
-- Name: user_agent_access; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.user_agent_access (
    id integer NOT NULL,
    user_id integer NOT NULL,
    agent_id integer NOT NULL,
    granted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_agent_access OWNER TO adk_dev_user;

--
-- Name: user_agent_access_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.user_agent_access_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_agent_access_id_seq OWNER TO adk_dev_user;

--
-- Name: user_agent_access_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.user_agent_access_id_seq OWNED BY public.user_agent_access.id;


--
-- Name: user_groups; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.user_groups (
    user_id integer NOT NULL,
    group_id integer NOT NULL,
    joined_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_groups OWNER TO adk_dev_user;

--
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.user_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    bio text,
    avatar_url text,
    preferences jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    theme character varying(50) DEFAULT 'light'::character varying,
    language character varying(10) DEFAULT 'en'::character varying,
    timezone character varying(50) DEFAULT 'UTC'::character varying
);


ALTER TABLE public.user_profiles OWNER TO adk_dev_user;

--
-- Name: user_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.user_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_profiles_id_seq OWNER TO adk_dev_user;

--
-- Name: user_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.user_profiles_id_seq OWNED BY public.user_profiles.id;


--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.user_sessions (
    id integer NOT NULL,
    session_id character varying(255) NOT NULL,
    user_id integer NOT NULL,
    active_agent_id integer,
    active_corpora text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_activity timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp without time zone,
    is_active boolean DEFAULT true,
    message_count integer DEFAULT 0,
    user_query_count integer DEFAULT 0
);


ALTER TABLE public.user_sessions OWNER TO adk_dev_user;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.user_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_sessions_id_seq OWNER TO adk_dev_user;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.user_sessions_id_seq OWNED BY public.user_sessions.id;


--
-- Name: user_stats; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.user_stats (
    id integer NOT NULL,
    user_id integer NOT NULL,
    total_queries integer DEFAULT 0,
    total_sessions integer DEFAULT 0,
    last_query_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_stats OWNER TO adk_dev_user;

--
-- Name: user_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.user_stats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_stats_id_seq OWNER TO adk_dev_user;

--
-- Name: user_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.user_stats_id_seq OWNED BY public.user_stats.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: adk_dev_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    hashed_password character varying(255),
    google_id character varying(255),
    auth_provider character varying(50) DEFAULT 'local'::character varying,
    is_active boolean DEFAULT true,
    default_agent_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp without time zone
);


ALTER TABLE public.users OWNER TO adk_dev_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: adk_dev_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO adk_dev_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adk_dev_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: agents id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.agents ALTER COLUMN id SET DEFAULT nextval('public.agents_id_seq'::regclass);


--
-- Name: chat_sessions id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.chat_sessions ALTER COLUMN id SET DEFAULT nextval('public.chat_sessions_id_seq'::regclass);


--
-- Name: corpora id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpora ALTER COLUMN id SET DEFAULT nextval('public.corpora_id_seq'::regclass);


--
-- Name: corpus_audit_log id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_audit_log ALTER COLUMN id SET DEFAULT nextval('public.corpus_audit_log_id_seq'::regclass);


--
-- Name: corpus_metadata id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_metadata ALTER COLUMN id SET DEFAULT nextval('public.corpus_metadata_id_seq'::regclass);


--
-- Name: document_access_log id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.document_access_log ALTER COLUMN id SET DEFAULT nextval('public.document_access_log_id_seq'::regclass);


--
-- Name: group_corpus_access id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_corpus_access ALTER COLUMN id SET DEFAULT nextval('public.group_corpus_access_id_seq'::regclass);


--
-- Name: groups id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.groups ALTER COLUMN id SET DEFAULT nextval('public.groups_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: session_corpus_selections id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.session_corpus_selections ALTER COLUMN id SET DEFAULT nextval('public.session_corpus_selections_id_seq'::regclass);


--
-- Name: user_agent_access id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_agent_access ALTER COLUMN id SET DEFAULT nextval('public.user_agent_access_id_seq'::regclass);


--
-- Name: user_profiles id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_profiles ALTER COLUMN id SET DEFAULT nextval('public.user_profiles_id_seq'::regclass);


--
-- Name: user_sessions id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_sessions ALTER COLUMN id SET DEFAULT nextval('public.user_sessions_id_seq'::regclass);


--
-- Name: user_stats id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_stats ALTER COLUMN id SET DEFAULT nextval('public.user_stats_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: agents; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.agents (id, name, description, instructions, model, temperature, top_p, top_k, is_active, created_at, updated_at, display_name, config_path) FROM stdin;
1	default_agent	Default RAG agent with multi-corpus support	\N	gemini-2.0-flash-exp	0.7	0.95	40	t	2026-01-19 16:25:13.057053	2026-01-19 16:25:13.057053	Default RAG Agent	default_agent
\.


--
-- Data for Name: chat_sessions; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.chat_sessions (id, user_id, agent_id, title, message_count, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: corpora; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.corpora (id, name, display_name, description, gcs_bucket, vertex_corpus_id, is_active, created_at, updated_at) FROM stdin;
7	hacker-books	hacker-books	Synced from Vertex AI		projects/adk-rag-ma/locations/us-west1/ragCorpora/4611686018427387904	t	2026-01-19 22:23:47.376329	2026-01-19 22:23:47.375606
4	management	management	Synced from Vertex AI on 2026-01-07T21:43:00.126967	gs://adk-rag-ma-management	projects/adk-rag-ma/locations/us-west1/ragCorpora/6838716034162098176	t	2026-01-19 18:31:06.339497	2026-01-19 18:31:06.338859
2	test-corpus	Test Corpus	Test corpus for development	test-bucket	projects/adk-rag-ma/locations/us-west1/ragCorpora/6917529027641081856	t	2026-01-19 18:20:06.716618	2026-01-19 18:20:06.71621
6	semantic-web	semantic-web	Synced from Vertex AI		projects/adk-rag-ma/locations/us-west1/ragCorpora/4749045807062188032	t	2026-01-19 18:31:06.346178	2026-01-19 18:31:06.345476
11	develom-general	Develom General Knowledge	General knowledge base for Develom organization	develom-documents	\N	f	2026-01-25 20:09:02.1404	2026-01-25 20:09:02.1404
1	ai-books	AI Books Collection	Collection of AI and technology books	ipad-book-collection	projects/adk-rag-ma/locations/us-west1/ragCorpora/2305843009213693952	t	2026-01-18 23:53:30.544567	2026-01-18 23:53:30.544567
3	design	design	Synced from Vertex AI on 2026-01-07T21:43:00.123602	gs://adk-rag-ma-design	projects/adk-rag-ma/locations/us-west1/ragCorpora/3379951520341557248	t	2026-01-19 18:20:54.233976	2026-01-19 18:20:54.233547
14	usfs-corpora	usfs-corpora	Synced from Vertex AI on 2026-01-07T21:43:00.130858	gs://adk-rag-ma-usfs-corpora	projects/adk-rag-ma/locations/us-west1/ragCorpora/137359788634800128	f	2026-01-25 20:09:02.1404	2026-01-25 20:09:02.1404
5	recipes	recipes	Synced from Vertex AI on 2026-01-08T12:55:42.546437	gs://adk-rag-ma-recipes	projects/adk-rag-ma/locations/us-west1/ragCorpora/4532873024948404224	t	2026-01-19 18:31:06.343156	2026-01-19 18:31:06.342518
16	fiction	fiction	Synced from Vertex AI on 2026-01-08T11:36:05.531300	gs://adk-rag-ma-fiction	projects/adk-rag-ma/locations/us-west1/ragCorpora/7991637538768945152	f	2026-01-25 20:09:02.1404	2026-01-25 20:09:02.1404
\.


--
-- Data for Name: corpus_audit_log; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.corpus_audit_log (id, corpus_id, user_id, action, changes, metadata, "timestamp") FROM stdin;
1	1	1	test_action	{"test": "data"}	\N	2026-01-19 18:47:49.006971
2	1	1	created	{"test": "value"}	{"source": "test"}	2026-01-19 20:33:57.466456
3	1	1	created	{"test": "value_0"}	{"source": "test", "iteration": 0}	2026-01-19 20:35:08.722308
4	1	1	created	{"test": "value_1"}	{"source": "test", "iteration": 1}	2026-01-19 20:35:08.81624
5	1	1	created	{"test": "value_2"}	{"source": "test", "iteration": 2}	2026-01-19 20:35:08.818591
6	\N	1	deleted_user	{"target_user_id": 7, "username": "Robert"}	{"operation": "user_delete"}	2026-01-19 22:00:05.91968
7	\N	1	deleted_user	{"target_user_id": 7, "username": "Robert"}	{"operation": "user_delete"}	2026-01-19 22:00:20.851958
8	\N	1	deleted_user	{"target_user_id": 7, "username": "Robert"}	{"operation": "user_delete"}	2026-01-19 22:20:08.243381
9	\N	1	assigned_user_to_group	{"target_user_id": 5, "group_id": 2, "username": "hector", "group_name": "admin-users"}	{"operation": "user_group_assignment"}	2026-01-19 22:21:19.910946
10	\N	1	assigned_user_to_group	{"target_user_id": 5, "group_id": 1, "username": "hector", "group_name": "users"}	{"operation": "user_group_assignment"}	2026-01-19 22:21:30.784641
11	\N	1	deleted_user	{"target_user_id": 6, "username": "octavio"}	{"operation": "user_delete"}	2026-01-19 22:21:58.903571
12	\N	1	deleted_user	{"target_user_id": 6, "username": "octavio"}	{"operation": "user_delete"}	2026-01-19 22:22:07.776319
13	7	1	created	{"source": "vertex_ai_sync"}	{"operation": "sync"}	2026-01-19 22:23:47.384436
14	\N	1	deleted_user	{"target_user_id": 6, "username": "octavio"}	{"operation": "user_delete"}	2026-01-19 22:25:55.755282
15	\N	1	deleted_user	{"target_user_id": 8, "username": "testuser_1768859726"}	{"operation": "user_delete"}	2026-01-19 22:36:19.44596
16	\N	5	deleted_user	{"target_user_id": 8, "username": "testuser_1768859726"}	{"operation": "user_delete"}	2026-01-19 22:37:46.958492
17	\N	5	deleted_user	{"target_user_id": 8, "username": "testuser_1768859726"}	{"operation": "user_delete"}	2026-01-19 22:40:58.41177
18	\N	5	created_user	{"new_user_id": 9, "username": "testuser999", "groups": []}	{"operation": "user_create"}	2026-01-19 22:43:04.79351
19	\N	5	deleted_user	{"target_user_id": 9, "username": "testuser999"}	{"operation": "user_delete"}	2026-01-19 22:44:59.114378
20	\N	5	deleted_user	{"target_user_id": 9, "username": "testuser999"}	{"operation": "user_delete"}	2026-01-19 22:47:32.018588
21	\N	5	deleted_user	{"target_user_id": 9, "username": "testuser999"}	{"operation": "user_delete"}	2026-01-19 22:49:45.504572
22	\N	5	deleted_user	{"target_user_id": 7, "username": "Robert"}	{"operation": "user_delete"}	2026-01-19 22:51:24.235244
23	\N	1	deleted_user	{"target_user_id": 6, "username": "octavio"}	{"operation": "user_delete"}	2026-01-19 22:57:56.325478
24	\N	1	deleted_user	{"target_user_id": 8, "username": "testuser_1768859726"}	{"operation": "user_delete"}	2026-01-19 22:58:11.108824
25	\N	1	deleted_user	{"target_user_id": 4, "username": "test_user_1768858532"}	{"operation": "user_delete"}	2026-01-19 22:59:14.170656
26	\N	5	created_user	{"new_user_id": 10, "username": "robert", "groups": []}	{"operation": "user_create"}	2026-01-19 23:11:14.908001
27	\N	1	created_user	{"new_user_id": 11, "username": "mila", "groups": [2]}	{"operation": "user_create"}	2026-01-19 23:28:36.984507
28	\N	1	assigned_user_to_group	{"target_user_id": 10, "group_id": 2, "username": "robert", "group_name": "admin-users"}	{"operation": "user_group_assignment"}	2026-01-19 23:28:54.387974
29	\N	5	assigned_user_to_group	{"target_user_id": 10, "group_id": 2, "username": "robert", "group_name": "admin-users"}	{"operation": "user_group_assignment"}	2026-01-19 23:33:04.103464
30	\N	5	assigned_user_to_group	{"target_user_id": 10, "group_id": 2, "username": "robert", "group_name": "admin-users"}	{"operation": "user_group_assignment"}	2026-01-19 23:33:04.388302
31	\N	1	updated_user	{"target_user_id": 10, "updates": {"is_active": false}, "password_reset": false}	{"operation": "user_update"}	2026-01-19 23:38:14.141359
32	\N	5	created_user	{"new_user_id": 13, "username": "Robert", "groups": [2]}	{"operation": "user_create"}	2026-01-19 23:45:10.526898
33	\N	1	assigned_user_to_group	{"target_user_id": 11, "group_id": 1, "username": "mila", "group_name": "users"}	{"operation": "user_group_assignment"}	2026-01-19 23:47:14.922688
34	\N	1	assigned_user_to_group	{"target_user_id": 11, "group_id": 1, "username": "mila", "group_name": "users"}	{"operation": "user_group_assignment"}	2026-01-19 23:47:17.142938
35	\N	1	deleted_user	{"target_user_id": 13, "username": "Robert"}	{"operation": "user_delete"}	2026-01-20 16:40:29.190197
36	\N	1	created_user	{"new_user_id": 15, "username": "test-writer", "groups": [1]}	{"operation": "user_create"}	2026-01-20 16:43:03.824762
37	1	1	updated	{"before": {"id": 1, "corpus_id": 1, "created_by": null, "created_at": "2026-01-18T23:53:30.544567", "last_synced_at": null, "last_synced_by": null, "sync_status": "active", "sync_error_message": null, "document_count": 0, "last_document_count_update": null, "tags": "ai, books, ai books, artificial intelligence", "notes": "first book collection uploaded for testing", "created_by_name": null, "last_synced_by_name": null}, "after": {"id": 1, "corpus_id": 1, "created_by": null, "created_at": "2026-01-18T23:53:30.544567", "last_synced_at": null, "last_synced_by": null, "sync_status": "active", "sync_error_message": null, "document_count": 0, "last_document_count_update": null, "tags": "ai, books, ai books, artificial intelligence", "notes": "first book collection uploaded for testing", "created_by_name": null, "last_synced_by_name": null}, "fields": ["tags", "notes"]}	{"operation": "update_metadata"}	2026-01-20 17:01:19.91456
38	3	1	updated	{"before": {"id": 3, "corpus_id": 3, "created_by": null, "created_at": "2026-01-19T18:24:59.144004", "last_synced_at": null, "last_synced_by": null, "sync_status": "active", "sync_error_message": null, "document_count": 0, "last_document_count_update": null, "tags": "design corpus", "notes": "This corpus only has one document.", "created_by_name": null, "last_synced_by_name": null}, "after": {"id": 3, "corpus_id": 3, "created_by": null, "created_at": "2026-01-19T18:24:59.144004", "last_synced_at": null, "last_synced_by": null, "sync_status": "active", "sync_error_message": null, "document_count": 0, "last_document_count_update": null, "tags": "design corpus", "notes": "This corpus only has one document.", "created_by_name": null, "last_synced_by_name": null}, "fields": ["tags", "notes"]}	{"operation": "update_metadata"}	2026-01-20 17:01:35.802106
39	1	1	deactivated	{"before": {"is_active": true}, "after": {"is_active": false}}	{"operation": "update_status"}	2026-01-20 17:10:25.874249
40	1	1	activated	{"before": {"is_active": false}, "after": {"is_active": true}}	{"operation": "update_status"}	2026-01-20 17:10:37.619795
41	1	1	deactivated	{"before": {"is_active": true}, "after": {"is_active": false}}	{"operation": "update_status"}	2026-01-20 17:10:50.228939
42	1	1	activated	{"before": {"is_active": false}, "after": {"is_active": true}}	{"operation": "update_status"}	2026-01-20 17:10:53.6028
43	1	1	deactivated	{"before": {"is_active": true}, "after": {"is_active": false}}	{"operation": "update_status"}	2026-01-20 17:10:54.567622
44	1	1	activated	{"before": {"is_active": false}, "after": {"is_active": true}}	{"operation": "update_status"}	2026-01-20 17:10:56.107837
45	4	1	deactivated	{"before": {"is_active": true}, "after": {"is_active": false}}	{"operation": "update_status"}	2026-01-20 17:11:06.465659
46	5	1	deactivated	{"before": {"is_active": true}, "after": {"is_active": false}}	{"operation": "update_status"}	2026-01-20 17:11:08.843618
47	5	1	activated	{"before": {"is_active": false}, "after": {"is_active": true}}	{"operation": "update_status"}	2026-01-20 17:11:09.800587
48	4	1	activated	{"before": {"is_active": false}, "after": {"is_active": true}}	{"operation": "update_status"}	2026-01-20 17:11:11.051575
49	4	1	deactivated	{"before": {"is_active": true}, "after": {"is_active": false}}	{"operation": "update_status"}	2026-01-20 17:11:13.761817
50	4	1	updated	{"before": {"id": 4, "corpus_id": 4, "created_by": null, "created_at": "2026-01-19T18:34:22.276655", "last_synced_at": null, "last_synced_by": null, "sync_status": "active", "sync_error_message": null, "document_count": 0, "last_document_count_update": null, "tags": null, "notes": null, "created_by_name": null, "last_synced_by_name": null}, "after": {"id": 4, "corpus_id": 4, "created_by": null, "created_at": "2026-01-19T18:34:22.276655", "last_synced_at": null, "last_synced_by": null, "sync_status": "active", "sync_error_message": null, "document_count": 0, "last_document_count_update": null, "tags": "corpus, management, corpus access", "notes": "Corpus management", "created_by_name": null, "last_synced_by_name": null}, "fields": ["tags", "notes"]}	{"operation": "update_metadata"}	2026-01-20 17:27:52.903024
51	5	1	updated	{"before": {"id": 5, "corpus_id": 5, "created_by": null, "created_at": "2026-01-19T18:34:44.973240", "last_synced_at": "2026-01-20T17:37:54.427023", "last_synced_by": 1, "sync_status": "active", "sync_error_message": null, "document_count": 0, "last_document_count_update": null, "tags": null, "notes": null, "created_by_name": null, "last_synced_by_name": "testuser"}, "after": {"id": 5, "corpus_id": 5, "created_by": null, "created_at": "2026-01-19T18:34:44.973240", "last_synced_at": "2026-01-20T17:37:54.427023", "last_synced_by": 1, "sync_status": "active", "sync_error_message": null, "document_count": 0, "last_document_count_update": null, "tags": "recipes", "notes": "A couple of Indian recipes found online. Enjoy.", "created_by_name": null, "last_synced_by_name": "testuser"}, "fields": ["tags", "notes"]}	{"operation": "update_metadata"}	2026-01-20 17:39:21.93363
52	3	1	granted_access	{"group_id": 1, "permission": "read"}	{"operation": "grant_permission"}	2026-01-20 17:51:19.995158
53	7	1	granted_access	{"group_id": 1, "permission": "read"}	{"operation": "grant_permission"}	2026-01-20 17:51:21.125509
54	5	1	granted_access	{"group_id": 1, "permission": "read"}	{"operation": "grant_permission"}	2026-01-20 17:51:22.249372
55	6	1	granted_access	{"group_id": 1, "permission": "read"}	{"operation": "grant_permission"}	2026-01-20 17:51:23.31005
56	2	1	granted_access	{"group_id": 1, "permission": "read"}	{"operation": "grant_permission"}	2026-01-20 17:51:24.634989
57	7	1	granted_access	{"group_id": 2, "permission": "read"}	{"operation": "grant_permission"}	2026-01-20 17:51:45.608276
58	7	1	revoked_access	{"group_id": 1}	{"operation": "revoke_permission"}	2026-01-20 17:51:46.941636
59	7	1	granted_access	{"group_id": 3, "permission": "read"}	{"operation": "grant_permission"}	2026-01-20 17:51:49.728596
60	7	1	revoked_access	{"group_id": 2}	{"operation": "revoke_permission"}	2026-01-20 17:51:54.119857
61	7	5	granted_access	{"group_id": 2, "permission": "read"}	{"operation": "grant_permission"}	2026-01-25 21:08:08.632471
\.


--
-- Data for Name: corpus_metadata; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.corpus_metadata (id, corpus_id, created_by, created_at, last_synced_at, last_synced_by, sync_status, sync_error_message, document_count, last_document_count_update, tags, notes) FROM stdin;
1	1	\N	2026-01-18 23:53:30.544567	2026-01-20 17:49:07.201372	1	active	\N	148	2026-01-20 17:49:07.208408	ai, books, ai books, artificial intelligence	first book collection uploaded for testing
3	3	\N	2026-01-19 18:24:59.144004	2026-01-20 17:49:07.584193	1	active	\N	1	2026-01-20 17:49:07.588143	design corpus	This corpus only has one document.
7	7	1	2026-01-19 22:23:47.379997	2026-01-20 17:49:07.961716	1	active	\N	0	2026-01-20 17:49:07.965937	\N	\N
4	4	\N	2026-01-19 18:34:22.276655	2026-01-20 17:49:08.312346	1	active	\N	3	2026-01-20 17:49:08.315649	corpus, management, corpus access	Corpus management
5	5	\N	2026-01-19 18:34:44.97324	2026-01-20 17:49:09.106625	1	active	\N	41	2026-01-20 17:49:09.108969	recipes	A couple of Indian recipes found online. Enjoy.
6	6	\N	2026-01-19 18:35:47.309926	2026-01-20 17:49:09.479139	1	active	\N	1	2026-01-20 17:49:09.482314	\N	\N
2	2	\N	2026-01-19 18:20:18.6582	2026-01-20 17:49:09.829012	1	active	\N	0	2026-01-20 17:49:09.832548	\N	\N
8	11	\N	2026-01-25 20:54:09.958602	\N	\N	active	\N	0	\N	\N	\N
9	16	\N	2026-01-25 20:54:09.983469	\N	\N	active	\N	0	\N	\N	\N
10	14	\N	2026-01-25 20:54:10.033434	\N	\N	active	\N	0	\N	\N	\N
\.


--
-- Data for Name: document_access_log; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.document_access_log (id, user_id, corpus_id, document_name, document_file_id, access_type, success, error_message, source_uri, ip_address, user_agent, accessed_at) FROM stdin;
1	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 00:07:21.799016
2	1	1	test.pdf	\N	view	f	Document not found in corpus	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 00:13:45.320975
3	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 00:14:17.321782
4	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 00:16:53.776549
5	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 16:05:30.357205
6	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 16:20:50.404343
7	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 16:22:11.286687
8	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 16:38:52.02729
9	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 16:39:21.2054
10	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	curl/8.7.1	2026-01-19 16:41:49.682562
11	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	curl/8.7.1	2026-01-19 16:47:41.951694
12	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	curl/8.7.1	2026-01-19 16:48:21.708079
13	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	\N	127.0.0.1	curl/8.7.1	2026-01-19 16:49:28.64617
14	1	1	DataStructures.pdf	5584740416008279038	view	f	Failed to generate signed URL	gs://develom-documents/DataStructures.pdf	127.0.0.1	curl/8.7.1	2026-01-19 16:50:54.314491
15	1	1	DataStructures.pdf	5584740416008279038	view	f	Failed to generate signed URL	gs://develom-documents/DataStructures.pdf	127.0.0.1	curl/8.7.1	2026-01-19 16:51:17.320353
16	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	gs://develom-documents/DataStructures.pdf	127.0.0.1	curl/8.7.1	2026-01-19 16:52:33.949732
17	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	gs://develom-documents/DataStructures.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 16:58:42.030589
18	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	gs://develom-documents/DataStructures.pdf	127.0.0.1	curl/8.7.1	2026-01-19 17:16:43.27202
19	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	gs://develom-documents/DataStructures.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 17:36:17.467172
20	1	1	DataStructures.pdf	5584740416008279038	view	t	\N	gs://develom-documents/DataStructures.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-19 18:55:45.041707
21	1	5	vegan	\N	view	f	Document not found in corpus	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-20 19:53:13.974209
22	1	1	Pancake.md	\N	view	f	Document not found in corpus	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-20 19:54:47.626294
23	1	5	Pancake.md	5606864069428468589	view	t	\N	gs://usfs-corpora/corpus-recipes/Pancake.md	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-20 19:55:02.130983
24	5	1	Beginning Nodejs.pdf	5584740117428586717	view	t	\N	gs://develom-documents/Beginning Nodejs.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-20 20:59:06.700516
25	5	1	beyond-the-twelve-factor-app.pdf	5584740533130961114	view	t	\N	gs://develom-documents/beyond-the-twelve-factor-app.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-20 21:00:48.847298
26	5	1	Beginning Nodejs.pdf	5584740117428586717	view	t	\N	gs://develom-documents/Beginning Nodejs.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-20 21:01:22.29665
27	5	1	building-an-optimized-business.pdf	5584740882971893901	view	t	\N	gs://develom-documents/building-an-optimized-business.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-20 21:01:32.700138
28	5	1	security_concepts.pdf	5584741116908904937	view	t	\N	gs://develom-documents/security_concepts.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:30:37.338222
29	5	1	security_concepts.pdf	5584741116908904937	view	t	\N	gs://develom-documents/security_concepts.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:30:41.269758
30	5	1	building_secure_and_reliable_systems.pdf	5584741302950752719	view	t	\N	gs://develom-documents/building_secure_and_reliable_systems.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:37:02.786375
31	5	1	building_secure_and_reliable_systems.pdf	5584741302950752719	view	t	\N	gs://develom-documents/building_secure_and_reliable_systems.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:37:04.306263
32	5	1	building_secure_and_reliable_systems.pdf	5584741302950752719	view	t	\N	gs://develom-documents/building_secure_and_reliable_systems.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:37:29.627208
33	5	1	building_secure_and_reliable_systems.pdf	5584741302950752719	view	t	\N	gs://develom-documents/building_secure_and_reliable_systems.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:37:50.163329
83	5	1	1007149.pdf	5584739984634514644	view	t	\N	gs://develom-documents/1007149.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:59:23.441241
34	5	1	building-an-optimized-business.pdf	5584740882971893901	view	t	\N	gs://develom-documents/building-an-optimized-business.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:38:01.284927
35	5	1	devopssec.pdf	5584740637489174849	view	t	\N	gs://develom-documents/devopssec.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:38:22.564678
36	5	1	vdoc.pub_software-security-engineering-a-guide-for-project-managers-a-guide-for-project-managers-sei-series-in-software-engineering.pdf	5584741069588491626	view	t	\N	gs://develom-documents/vdoc.pub_software-security-engineering-a-guide-for-project-managers-a-guide-for-project-managers-sei-series-in-software-engineering.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:38:57.741443
37	5	1	vdoc.pub_software-security-engineering-a-guide-for-project-managers-a-guide-for-project-managers-sei-series-in-software-engineering.pdf	5584741069588491626	view	t	\N	gs://develom-documents/vdoc.pub_software-security-engineering-a-guide-for-project-managers-a-guide-for-project-managers-sei-series-in-software-engineering.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:38:59.164502
38	5	1	vdoc.pub_forensic-discovery.pdf	5584740706492976811	view	t	\N	gs://develom-documents/vdoc.pub_forensic-discovery.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:40:48.688017
39	5	1	vdoc.pub_forensic-discovery.pdf	5584740706492976811	view	t	\N	gs://develom-documents/vdoc.pub_forensic-discovery.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 00:40:50.460674
40	5	1	vdoc.pub_forensic-discovery.pdf	5584740706492976811	view	t	\N	gs://develom-documents/vdoc.pub_forensic-discovery.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 02:41:42.817127
41	5	1	vdoc.pub_forensic-discovery.pdf	5584740706492976811	view	t	\N	gs://develom-documents/vdoc.pub_forensic-discovery.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 02:41:44.423638
42	5	1	2205.09510v4.pdf	5584739964502412332	view	t	\N	gs://develom-documents/2205.09510v4.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 02:44:19.857803
43	5	1	Artificial Intelligence and Evaluation_24_11_25_10_02_42.pdf	5584740161368698371	view	t	\N	gs://develom-documents/Artificial Intelligence and Evaluation_24_11_25_10_02_42.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 02:44:39.400662
44	5	1	cloud-native-devops-k8s-2e.pdf	5584740941515965344	view	t	\N	gs://develom-documents/cloud-native-devops-k8s-2e.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 02:46:03.419039
45	5	1	vdoc.pub_forensic-discovery.pdf	5584740706492976811	view	t	\N	gs://develom-documents/vdoc.pub_forensic-discovery.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 02:48:58.964817
46	5	1	vdoc.pub_forensic-discovery.pdf	5584740706492976811	view	t	\N	gs://develom-documents/vdoc.pub_forensic-discovery.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 02:49:00.682032
47	5	1	vdoc.pub_forensic-discovery.pdf	5584740706492976811	view	t	\N	gs://develom-documents/vdoc.pub_forensic-discovery.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 03:04:02.749678
48	5	1	vdoc.pub_forensic-discovery.pdf	5584740706492976811	view	t	\N	gs://develom-documents/vdoc.pub_forensic-discovery.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 03:04:04.027031
49	5	1	oreilly-cloud-native-archx.pdf	5584740644190620132	view	t	\N	gs://develom-documents/oreilly-cloud-native-archx.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 03:04:20.24305
50	5	1	1001824.pdf	5584740003892657598	view	t	\N	gs://develom-documents/1001824.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 03:06:32.510514
51	5	1	linuxbasicsforhackers.pdf	5584741181442413462	view	t	\N	gs://develom-documents/linuxbasicsforhackers.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-21 03:06:59.054407
52	5	1	DataStructures.pdf	5584740416008279038	view	t	\N	gs://develom-documents/DataStructures.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-25 20:56:19.777033
53	5	1	2019BurkovTheHundred-pageMachineLearning.pdf	5584739954916301485	view	t	\N	gs://develom-documents/2019BurkovTheHundred-pageMachineLearning.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-25 21:32:44.95797
54	5	3	Responsive Web Design.pdf	5606249237440561091	view	t	\N	gs://usfs-corpora/corpus-design/Responsive Web Design.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-25 21:33:00.212571
55	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-25 21:33:30.542104
56	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-25 21:33:41.155384
57	5	5	Beignet.md	5606864058810246103	view	t	\N	gs://usfs-corpora/corpus-recipes/Beignet.md	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-25 21:34:27.916486
58	5	6	Linked Open Data - The Essentials.pdf	5606989244506046056	view	t	\N	gs://usfs-corpora/corpus-semantic-web/Linked Open Data - The Essentials.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-25 21:34:40.589037
59	5	1	2205.09510v4.pdf	5584739964502412332	view	t	\N	gs://develom-documents/2205.09510v4.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 00:18:20.960368
60	5	1	2106.10165v2.pdf	5584740201430836163	view	t	\N	gs://develom-documents/2106.10165v2.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 00:18:45.094619
61	5	1	DataStructures.pdf	5584740416008279038	view	t	\N	gs://develom-documents/DataStructures.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 00:21:38.740593
62	5	6	Linked Open Data - The Essentials.pdf	5606989244506046056	view	t	\N	gs://usfs-corpora/corpus-semantic-web/Linked Open Data - The Essentials.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 01:59:29.980825
63	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:09:08.0142
64	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:09:18.529658
65	5	3	Responsive Web Design.pdf	5606249237440561091	view	t	\N	gs://usfs-corpora/corpus-design/Responsive Web Design.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:15:18.486065
66	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:17:56.263893
67	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:19:24.274481
68	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:19:34.311169
69	5	4	The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	5606251028164798032	view	t	\N	gs://usfs-corpora/corpus-management/The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:19:51.076921
70	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:20:01.197713
71	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:21:57.757144
72	5	4	The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	5606251028164798032	view	t	\N	gs://usfs-corpora/corpus-management/The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 02:22:36.476243
73	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 03:18:06.254287
74	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:42:24.603922
75	5	1	Bayesian Methods for Hackers Probabilistic Programming and Bayesian Inference 2.pdf	5584740096187739269	view	t	\N	gs://develom-documents/Bayesian Methods for Hackers Probabilistic Programming and Bayesian Inference 2.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:42:36.011698
76	5	1	Bayesian Methods for Hackers Probabilistic Programming and Bayesian Inference.pdf	5584740105698064037	view	t	\N	gs://develom-documents/Bayesian Methods for Hackers Probabilistic Programming and Bayesian Inference.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:43:07.608329
77	5	1	d5bbd7101305d35f84c6bac5773f0320.pdf	5584740792400800631	view	t	\N	gs://develom-documents/d5bbd7101305d35f84c6bac5773f0320.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:43:30.285546
78	5	3	Responsive Web Design.pdf	5606249237440561091	view	t	\N	gs://usfs-corpora/corpus-design/Responsive Web Design.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:44:48.397586
79	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:45:05.509908
80	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:59:06.466589
81	5	1	1001824.pdf	5584740003892657598	view	t	\N	gs://develom-documents/1001824.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:59:17.085269
82	5	1	1007149.pdf	5584739984634514644	view	t	\N	gs://develom-documents/1007149.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:59:22.610726
84	5	1	2019BurkovTheHundred-pageMachineLearning.pdf	5584739954916301485	view	t	\N	gs://develom-documents/2019BurkovTheHundred-pageMachineLearning.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:59:30.430698
85	5	1	978-1-4842-5574-2.pdf	5584740057792768458	view	t	\N	gs://develom-documents/978-1-4842-5574-2.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:59:37.302657
86	5	1	978-3-030-83944-4.pdf	5584739960433128956	view	t	\N	gs://develom-documents/978-3-030-83944-4.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:59:44.532334
87	5	3	Responsive Web Design.pdf	5606249237440561091	view	t	\N	gs://usfs-corpora/corpus-design/Responsive Web Design.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 04:59:53.666866
88	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 05:00:02.83396
89	5	5	Brownies-Vegan.md	5606864060955439546	view	t	\N	gs://usfs-corpora/corpus-recipes/Brownies-Vegan.md	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 05:00:58.212787
90	5	6	Linked Open Data - The Essentials.pdf	5606989244506046056	view	t	\N	gs://usfs-corpora/corpus-semantic-web/Linked Open Data - The Essentials.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 05:01:03.976722
91	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:30:53.449451
92	5	1	1001824.pdf	5584740003892657598	view	t	\N	gs://develom-documents/1001824.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:31:01.960258
93	5	1	1007149.pdf	5584739984634514644	view	t	\N	gs://develom-documents/1007149.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:31:11.619445
94	5	1	2019BurkovTheHundred-pageMachineLearning.pdf	\N	view	f	Document not found in corpus	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:31:27.382297
95	5	1	2020_Book_RationalCybersecurityForBusine.pdf	5584739999180926508	view	t	\N	gs://develom-documents/2020_Book_RationalCybersecurityForBusine.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:31:38.162356
96	5	1	2106.10165v2.pdf	\N	view	f	Document not found in corpus	\N	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:32:12.333002
97	5	1	2205.09510v4.pdf	5584739964502412332	view	t	\N	gs://develom-documents/2205.09510v4.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:32:17.335415
98	5	1	285_OOPS lecture notes Complete.pdf	5584739918850379756	view	t	\N	gs://develom-documents/285_OOPS lecture notes Complete.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:34:30.666857
99	5	1	789447725-Cybersecurity-Risks-of-AI-Generated-Code.pdf	5584739894513173605	view	t	\N	gs://develom-documents/789447725-Cybersecurity-Risks-of-AI-Generated-Code.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:34:42.445278
100	5	3	Responsive Web Design.pdf	5606249237440561091	view	t	\N	gs://usfs-corpora/corpus-design/Responsive Web Design.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:52:52.583588
101	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:55:47.995375
102	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-26 19:58:35.979674
103	5	1	1001824.pdf	5584740003892657598	view	t	\N	gs://develom-documents/1001824.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-28 20:29:01.325734
104	5	1	1007149.pdf	5584739984634514644	view	t	\N	gs://develom-documents/1007149.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-28 20:33:05.334124
105	5	1	978-1-4842-9711-7.pdf	5584739983517390247	view	t	\N	gs://develom-documents/978-1-4842-9711-7.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-28 20:33:13.45307
106	5	1	2019BurkovTheHundred-pageMachineLearning.pdf	5584739954916301485	view	t	\N	gs://develom-documents/2019BurkovTheHundred-pageMachineLearning.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-28 20:42:26.12558
107	5	3	Responsive Web Design.pdf	5606249237440561091	view	t	\N	gs://usfs-corpora/corpus-design/Responsive Web Design.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:26:07.771717
108	5	1	vdoc.pub_numpy-cookbook.pdf	5584740577166896781	view	t	\N	gs://develom-documents/vdoc.pub_numpy-cookbook.pdf	127.0.0.1	curl/8.7.1	2026-01-29 00:29:59.5618
109	5	1	vdoc.pub_numpy-cookbook.pdf	5584740577166896781	view	t	\N	gs://develom-documents/vdoc.pub_numpy-cookbook.pdf	127.0.0.1	curl/8.7.1	2026-01-29 00:40:50.681816
110	5	1	e64ed0cf1d791507372b901bbbfd73e3495c.pdf	5584740553935769902	view	t	\N	gs://develom-documents/e64ed0cf1d791507372b901bbbfd73e3495c.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:49:52.402376
111	5	1	evaluating-machine-learning-models.pdf	5584740591129899671	view	t	\N	gs://develom-documents/evaluating-machine-learning-models.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:50:14.402099
112	5	1	from-containers-to-kubernetes-with-nodejs.pdf	5584740768103710640	view	t	\N	gs://develom-documents/from-containers-to-kubernetes-with-nodejs.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:50:34.214964
113	5	1	from-containers-to-kubernetes-with-nodejs.pdf	5584740768103710640	view	t	\N	gs://develom-documents/from-containers-to-kubernetes-with-nodejs.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:50:49.094972
114	5	1	from-containers-to-kubernetes-with-nodejs.pdf	5584740768103710640	view	t	\N	gs://develom-documents/from-containers-to-kubernetes-with-nodejs.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:50:50.949483
115	5	1	from-containers-to-kubernetes-with-nodejs.pdf	5584740768103710640	view	t	\N	gs://develom-documents/from-containers-to-kubernetes-with-nodejs.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:50:52.797339
116	5	1	from-containers-to-kubernetes-with-nodejs.pdf	5584740768103710640	view	t	\N	gs://develom-documents/from-containers-to-kubernetes-with-nodejs.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:50:54.383334
117	5	1	from-containers-to-kubernetes-with-nodejs.pdf	5584740768103710640	view	t	\N	gs://develom-documents/from-containers-to-kubernetes-with-nodejs.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:51:01.945344
118	5	1	Fullstack_GraphQL Applications_with GRANDstack.pdf	5584740209015002819	view	t	\N	gs://develom-documents/Fullstack_GraphQL Applications_with GRANDstack.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:51:15.283017
119	5	5	Pizza-Simple-variant.md	5606864073521763326	view	t	\N	gs://usfs-corpora/corpus-recipes/Pizza-Simple-variant.md	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:52:17.649826
120	5	5	Pizza-Simple-variant.md	5606864073521763326	view	t	\N	gs://usfs-corpora/corpus-recipes/Pizza-Simple-variant.md	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:52:19.125011
121	5	5	Pizza-Simple-variant.md	5606864073521763326	view	t	\N	gs://usfs-corpora/corpus-recipes/Pizza-Simple-variant.md	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:52:20.523994
122	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:52:29.996702
123	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:52:37.873909
124	5	4	The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	5606251028164798032	view	t	\N	gs://usfs-corpora/corpus-management/The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:53:04.67727
125	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:53:13.988635
126	5	4	The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	5606251028164798032	view	t	\N	gs://usfs-corpora/corpus-management/The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:53:39.48867
127	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 00:55:40.161573
128	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:57:57.583333
129	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:58:11.379951
130	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 00:59:26.830108
131	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 01:03:22.926865
132	5	6	Linked Open Data - The Essentials.pdf	5606989244506046056	view	t	\N	gs://usfs-corpora/corpus-semantic-web/Linked Open Data - The Essentials.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 01:03:36.09899
133	5	3	Responsive Web Design.pdf	5606249237440561091	view	t	\N	gs://usfs-corpora/corpus-design/Responsive Web Design.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 01:03:58.170175
134	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 01:05:00.299701
135	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 01:06:50.596855
136	5	4	The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	5606251028164798032	view	t	\N	gs://usfs-corpora/corpus-management/The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 01:12:27.920305
137	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 03:16:22.189381
138	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 03:18:11.422044
139	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 03:34:53.999519
140	5	1	2205.09510v4.pdf	5584739964502412332	view	t	\N	gs://develom-documents/2205.09510v4.pdf	127.0.0.1	curl/8.7.1	2026-01-29 03:44:27.570892
141	5	1	2205.09510v4.pdf	5584739964502412332	view	t	\N	gs://develom-documents/2205.09510v4.pdf	127.0.0.1	curl/8.7.1	2026-01-29 03:50:53.286503
142	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 03:51:21.478732
143	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 03:51:22.068452
144	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 03:59:02.229483
145	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 04:07:10.2577
146	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	curl/8.7.1	2026-01-29 04:18:01.268542
147	5	1	0132366754_Jang_book.pdf	5584739968713799868	view	t	\N	gs://develom-documents/0132366754_Jang_book.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 04:42:06.980892
148	5	1	1001824.pdf	5584740003892657598	view	t	\N	gs://develom-documents/1001824.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 04:42:21.251177
149	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 04:42:30.533665
150	5	1	9783839474723.pdf	5584740003955854908	view	t	\N	gs://develom-documents/9783839474723.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:07:43.413561
151	5	1	9781138436923.pdf	5584740142030438123	view	t	\N	gs://develom-documents/9781138436923.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:00.333027
152	5	1	9781040027042.pdf	5584740064661085401	view	t	\N	gs://develom-documents/9781040027042.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:05.309138
153	5	1	978-981-19-5170-1.pdf	5584740064458025819	view	t	\N	gs://develom-documents/978-981-19-5170-1.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:09.644292
154	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:18.447593
155	5	4	The Bastard Operator From Hell.pdf	5606250881229310833	view	t	\N	gs://usfs-corpora/corpus-management/The Bastard Operator From Hell.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:21.747333
156	5	4	The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	5606251028164798032	view	t	\N	gs://usfs-corpora/corpus-management/The Minto Pyramid Principle - Logic in Writing, Thinking, & Problem Solving.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:25.249275
157	5	6	Linked Open Data - The Essentials.pdf	5606989244506046056	view	t	\N	gs://usfs-corpora/corpus-semantic-web/Linked Open Data - The Essentials.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:42.007631
158	5	6	Linked Open Data - The Essentials.pdf	5606989244506046056	view	t	\N	gs://usfs-corpora/corpus-semantic-web/Linked Open Data - The Essentials.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:50.05719
159	5	6	Linked Open Data - The Essentials.pdf	5606989244506046056	view	t	\N	gs://usfs-corpora/corpus-semantic-web/Linked Open Data - The Essentials.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:50.835019
160	5	6	Linked Open Data - The Essentials.pdf	5606989244506046056	view	t	\N	gs://usfs-corpora/corpus-semantic-web/Linked Open Data - The Essentials.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:08:51.734737
161	5	1	2106.10165v2.pdf	5584740201430836163	view	t	\N	gs://develom-documents/2106.10165v2.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:09:13.035091
162	5	1	789447725-Cybersecurity-Risks-of-AI-Generated-Code.pdf	5584739894513173605	view	t	\N	gs://develom-documents/789447725-Cybersecurity-Risks-of-AI-Generated-Code.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:09:19.700809
163	5	1	978-3-030-83944-4.pdf	5584739960433128956	view	t	\N	gs://develom-documents/978-3-030-83944-4.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:09:28.986182
164	5	1	9781040027042.pdf	5584740064661085401	view	t	\N	gs://develom-documents/9781040027042.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:09:36.618336
165	5	1	book_9780262378925.pdf	5584741082007216709	view	t	\N	gs://develom-documents/book_9780262378925.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:09:51.504252
166	5	1	building-an-optimized-business.pdf	5584740882971893901	view	t	\N	gs://develom-documents/building-an-optimized-business.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:10:00.752461
167	5	1	C++3e20120102.pdf	5584740285967014658	view	t	\N	gs://develom-documents/C++3e20120102.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:10:07.387468
168	5	1	cloud-native-devops-k8s-2e.pdf	5584740941515965344	view	t	\N	gs://develom-documents/cloud-native-devops-k8s-2e.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:10:12.696185
169	5	1	cloud-native-devops-k8s-2e.pdf	5584740941515965344	view	t	\N	gs://develom-documents/cloud-native-devops-k8s-2e.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:10:30.89627
170	5	1	cloud-native-devops-k8s-2e.pdf	5584740941515965344	view	t	\N	gs://develom-documents/cloud-native-devops-k8s-2e.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:10:32.287544
171	5	1	cloud-native-devops-k8s-2e.pdf	5584740941515965344	view	t	\N	gs://develom-documents/cloud-native-devops-k8s-2e.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:10:33.39663
172	5	1	cm-oreilly-kubernetes-patterns-ebook-f19824-201910-en.pdf	5584741027752504364	view	t	\N	gs://develom-documents/cm-oreilly-kubernetes-patterns-ebook-f19824-201910-en.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:10:49.292592
173	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:22:22.458165
174	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:22:23.311526
175	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:22:23.919748
176	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:22:24.769927
177	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:22:25.372061
178	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:56:47.579921
179	5	4	The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	5606250826521182911	view	t	\N	gs://usfs-corpora/corpus-management/The Lean Startup - How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.pdf	127.0.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15	2026-01-29 05:56:53.893533
\.


--
-- Data for Name: group_corpora; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.group_corpora (group_id, corpus_id) FROM stdin;
\.


--
-- Data for Name: group_corpus_access; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.group_corpus_access (id, group_id, corpus_id, permission, granted_at) FROM stdin;
9	8	14	read	2026-01-25 20:09:02.310987
10	9	2	admin	2026-01-25 20:09:02.310987
11	9	4	admin	2026-01-25 20:09:02.310987
12	11	1	read	2026-01-25 20:09:02.310987
13	2	3	admin	2026-01-25 20:09:02.310987
14	2	5	read	2026-01-25 20:09:02.310987
15	2	6	read	2026-01-25 20:09:02.310987
16	10	4	admin	2026-01-25 20:09:02.310987
17	10	14	admin	2026-01-25 20:09:02.310987
18	8	11	read	2026-01-25 20:09:02.310987
19	9	11	admin	2026-01-25 20:09:02.310987
20	10	16	read	2026-01-25 20:09:02.310987
21	2	4	admin	2026-01-25 20:09:02.310987
22	9	14	admin	2026-01-25 20:09:02.310987
23	8	1	read	2026-01-25 20:09:02.310987
24	11	3	read	2026-01-25 20:09:02.310987
25	10	11	admin	2026-01-25 20:09:02.310987
26	2	2	admin	2026-01-25 20:09:02.310987
27	11	4	read	2026-01-25 20:09:02.310987
28	10	1	admin	2026-01-25 20:09:02.310987
29	8	3	read	2026-01-25 20:09:02.310987
30	2	11	admin	2026-01-25 20:09:02.310987
31	2	14	admin	2026-01-25 20:09:02.310987
32	9	1	admin	2026-01-25 20:09:02.310987
33	11	14	read	2026-01-25 20:09:02.310987
34	12	11	read	2026-01-25 20:09:02.310987
35	8	2	read	2026-01-25 20:09:02.310987
36	8	4	read	2026-01-25 20:09:02.310987
37	9	3	admin	2026-01-25 20:09:02.310987
38	2	1	admin	2026-01-25 20:09:02.310987
39	10	3	admin	2026-01-25 20:09:02.310987
40	10	5	read	2026-01-25 20:09:02.310987
41	11	2	write	2026-01-25 20:09:02.310987
42	11	11	write	2026-01-25 20:09:02.310987
43	10	2	admin	2026-01-25 20:09:02.310987
44	2	7	read	2026-01-25 21:08:08.624896
\.


--
-- Data for Name: group_roles; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.group_roles (group_id, role_id) FROM stdin;
1	1
3	8
3	6
3	5
\.


--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.groups (id, name, description, is_active, created_at) FROM stdin;
1	users	Default user group	t	2026-01-18 23:38:44.091303
2	admin-users	Administrators with full system access	t	2026-01-18 23:54:48.728355
3	white-hacker	Group with white hacker permissions. 	t	2026-01-19 23:58:49.800793
7	admins	Administrators group with elevated privileges	t	2026-01-25 20:09:02.06542
8	viewers	Users with read-only access	t	2026-01-25 20:09:02.06542
9	managers	Managers with oversight access	t	2026-01-25 20:09:02.06542
10	developers	Software developers with full access	t	2026-01-25 20:09:02.06542
11	develom-group	Develom organization users	t	2026-01-25 20:09:02.06542
12	default-users	Default group for all users	t	2026-01-25 20:09:02.06542
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.roles (id, name, description, created_at, permissions) FROM stdin;
1	user	Standard user with read and query access	2026-01-18 23:38:44.090388	["read:corpora", "query:corpora", "read:documents", "read:agents"]
4	corpora-manager-role	Full corpus and document management	2026-01-20 00:32:30.754236	["read:corpora", "create:corpus", "update:corpus", "manage:corpora", "manage:corpus_access", "read:documents", "upload:documents", "delete:documents"]
3	admin-role	System administrator with full access	2026-01-20 00:31:41.955481	["admin:all"]
5	user-manager	Can manage users and group assignments	2026-01-20 06:07:47.171173	["read:users", "create:user", "update:user", "delete:user", "manage:users", "read:groups", "manage:user_groups"]
6	agent-manager	Can create and manage agents and their access	2026-01-20 06:07:47.173451	["read:agents", "create:agent", "update:agent", "delete:agent", "manage:agents", "manage:agent_access"]
7	corpus-viewer	Read-only access to corpora and documents	2026-01-20 06:07:47.174627	["read:corpora", "read:documents", "query:corpora"]
8	corpus-editor	Can edit corpora and upload documents	2026-01-20 06:07:47.175826	["read:corpora", "update:corpus", "read:documents", "upload:documents", "query:corpora"]
\.


--
-- Data for Name: session_corpus_selections; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.session_corpus_selections (id, user_id, corpus_id, last_selected_at) FROM stdin;
\.


--
-- Data for Name: user_agent_access; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.user_agent_access (id, user_id, agent_id, granted_at) FROM stdin;
1	1	1	2026-01-19 16:25:13.062904
\.


--
-- Data for Name: user_groups; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.user_groups (user_id, group_id, joined_at) FROM stdin;
1	1	2026-01-18 23:53:30.548017
1	2	2026-01-19 16:30:53.390172
4	2	2026-01-19 21:37:21.362613
8	2	2026-01-19 22:13:20.897287
5	2	2026-01-19 22:21:19.908008
5	1	2026-01-19 22:21:30.782226
9	2	2026-01-19 22:46:07.350638
11	2	2026-01-19 23:28:36.97966
10	2	2026-01-19 23:28:54.379262
13	2	2026-01-19 23:45:10.524093
11	1	2026-01-19 23:47:14.920441
15	1	2026-01-20 16:43:03.822396
15	2	2026-01-20 16:59:05.01165
16	2	2026-01-29 00:16:14.624425
\.


--
-- Data for Name: user_profiles; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.user_profiles (id, user_id, bio, avatar_url, preferences, created_at, updated_at, theme, language, timezone) FROM stdin;
1	8	\N	\N	\N	2026-01-19 21:55:26.98056	2026-01-19 21:55:26.98056	light	en	UTC
2	9	\N	\N	\N	2026-01-19 22:43:04.787797	2026-01-19 22:43:04.787797	light	en	UTC
3	10	\N	\N	\N	2026-01-19 23:11:14.901691	2026-01-19 23:11:14.901691	light	en	UTC
4	11	\N	\N	\N	2026-01-19 23:28:36.975625	2026-01-19 23:28:36.975625	light	en	UTC
5	13	\N	\N	\N	2026-01-19 23:45:10.519564	2026-01-19 23:45:10.519564	light	en	UTC
6	15	\N	\N	\N	2026-01-20 16:43:03.814337	2026-01-20 16:43:03.814337	light	en	UTC
7	1	\N	\N	{"selected_corpora": ["recipes"]}	2026-01-20 19:54:12.095943	2026-01-20 19:54:12.095943	light	en	UTC
9	16	\N	\N	\N	2026-01-29 00:06:43.812071	2026-01-29 00:06:43.812071	light	en	UTC
8	5	\N	\N	{"selected_corpora": ["management", "recipes"]}	2026-01-26 04:47:16.581505	2026-01-26 04:47:16.581505	light	en	UTC
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.user_sessions (id, session_id, user_id, active_agent_id, active_corpora, created_at, last_activity, expires_at, is_active, message_count, user_query_count) FROM stdin;
1	e6f0817a-fd47-4736-a9c5-408fc7971dbe	1	\N	\N	2026-01-19 16:28:10.725877	2026-01-19 16:28:10.725877	2026-01-20 16:28:10.726266	t	0	0
2	7661d2f4-6450-4c9d-a243-cadcfe96916a	1	\N	\N	2026-01-19 16:32:45.736588	2026-01-19 16:32:48.789	2026-01-20 16:32:45.736601	t	0	0
24	02beb507-b62d-4dd9-a8e4-1dc1295917e5	5	\N	\N	2026-01-24 01:23:32.738668	2026-01-24 01:23:36.445641	2026-01-25 01:23:32.739076	t	2	1
14	570ad4ff-9e23-452a-8d18-f6dd4813aa60	1	\N	\N	2026-01-20 19:10:34.273391	2026-01-20 19:25:43.295056	2026-01-21 19:10:34.273402	t	0	0
3	d46ba663-3588-431d-b9db-56302c7f3176	1	\N	\N	2026-01-19 16:36:04.173132	2026-01-19 16:38:08.606525	2026-01-20 16:36:04.173144	t	0	0
25	dbd462e3-b6db-42dc-86d6-2a2cf75031a7	5	\N	\N	2026-01-25 20:52:14.326406	2026-01-25 20:52:57.745219	2026-01-26 20:52:14.326417	t	6	3
15	8f8ce6f3-b1ba-4979-9ec3-a892288befaf	1	\N	\N	2026-01-20 19:26:34.111621	2026-01-20 19:29:04.083605	2026-01-21 19:26:34.111638	t	0	0
26	64a890b5-88d4-4316-a574-c599587a19f5	5	\N	\N	2026-01-25 20:57:01.661172	2026-01-25 20:57:38.138495	2026-01-26 20:57:01.661193	t	4	2
27	b84c140f-85dc-4425-8150-79af7b29a78f	5	\N	\N	2026-01-26 00:17:28.538348	2026-01-26 00:17:28.538348	2026-01-27 00:17:28.538366	t	0	0
5	d6e4d936-00df-4944-b5ae-cc06d51a4835	1	\N	\N	2026-01-19 18:04:45.046457	2026-01-19 18:04:49.386542	2026-01-20 18:04:45.046467	t	0	0
28	644c2657-a59b-4bb9-8685-02b13d18a922	5	\N	\N	2026-01-26 19:52:10.328032	2026-01-26 19:52:10.328032	2026-01-27 19:52:10.328054	t	0	0
4	b3b7825e-582b-4c82-bb1d-029e12759e44	1	\N	\N	2026-01-19 17:40:14.199639	2026-01-19 18:27:07.250368	2026-01-20 17:40:14.199664	t	0	0
6	fd221315-1929-493a-97bd-00aff01aa0cd	1	\N	\N	2026-01-19 20:10:25.942627	2026-01-19 20:10:39.032657	2026-01-20 20:10:25.942639	t	0	0
7	0dd33548-3a0a-478d-b080-9a5f4c38b859	1	\N	\N	2026-01-19 20:12:36.728351	2026-01-19 20:14:21.756313	2026-01-20 20:12:36.728363	t	0	0
29	8031bdf5-e1c4-414b-951b-f412ef212528	5	\N	\N	2026-01-26 19:52:10.345177	2026-01-26 19:52:22.108614	2026-01-27 19:52:10.345189	t	2	1
16	1c067946-a97d-44a2-b611-6e734e4bd983	1	\N	\N	2026-01-20 19:37:51.74254	2026-01-20 20:05:55.762901	2026-01-21 19:37:51.742564	t	10	5
8	b670203d-6b68-4f42-a31c-ac1778ce805e	1	\N	\N	2026-01-19 20:18:53.041549	2026-01-19 20:23:40.745966	2026-01-20 20:18:53.041559	t	0	0
30	363efb08-88b4-4289-be0d-3aaec288e7db	5	\N	\N	2026-01-26 20:06:06.671296	2026-01-26 20:06:26.535543	2026-01-27 20:06:06.671308	t	2	1
9	30e5faeb-3a6d-4d1c-8a8a-1c3b518d6808	1	\N	\N	2026-01-19 21:22:42.348108	2026-01-19 21:22:45.417089	2026-01-20 21:22:42.348118	t	0	0
10	46bbeffd-1909-4644-9969-28445d52771f	1	\N	\N	2026-01-19 21:25:05.186492	2026-01-19 21:25:16.0479	2026-01-20 21:25:05.186514	t	0	0
11	c362b2e9-2859-4b67-97ac-091f6d9d86a7	1	\N	\N	2026-01-19 22:19:34.167581	2026-01-19 22:19:35.637452	2026-01-20 22:19:34.167593	t	0	0
31	874ac18a-ea85-4b3f-a57a-b52b9f77b5c9	5	\N	\N	2026-01-28 20:34:46.86385	2026-01-28 20:35:02.105888	2026-01-29 20:34:46.863866	t	2	1
12	a010ad3a-69b5-4dae-b4be-9b3b68da82a5	1	\N	\N	2026-01-19 23:26:35.547751	2026-01-19 23:26:39.017421	2026-01-20 23:26:35.547764	t	0	0
13	3b99f2b9-9054-4f70-9619-c49f82917212	1	\N	\N	2026-01-20 00:31:00.660813	2026-01-20 00:31:04.996771	2026-01-21 00:31:00.660825	t	0	0
17	e350d214-6667-458e-9171-d8090aea4f2a	5	\N	\N	2026-01-20 20:40:16.134895	2026-01-20 21:03:11.538063	2026-01-21 20:40:16.134907	t	8	4
32	1be3a688-edf5-4b1e-a8fa-1f66add2d2ea	5	\N	\N	2026-01-29 05:12:03.293628	2026-01-29 05:12:11.651999	2026-01-30 05:12:03.293638	t	2	1
18	38ba59ce-36af-42ec-9468-441625de69c3	5	\N	\N	2026-01-20 22:40:32.023299	2026-01-20 22:43:40.104596	2026-01-21 22:40:32.02331	t	6	3
33	a856f7ea-f811-4b07-9018-f4de3b649985	5	\N	\N	2026-01-29 05:12:22.752558	2026-01-29 05:21:51.446552	2026-01-30 05:12:22.752568	t	22	11
21	2ee1682e-8e5d-4037-8dd8-078708d0f140	5	\N	\N	2026-01-21 00:03:59.699412	2026-01-21 02:47:44.089188	2026-01-22 00:03:59.699435	t	32	16
19	aa5bbc25-afd1-4a4c-9437-dabc8f928c4b	5	\N	\N	2026-01-20 23:34:41.698194	2026-01-20 23:35:46.378297	2026-01-21 23:34:41.698205	t	4	2
22	415a840d-7e3c-4542-a820-10a6ecb5d099	5	\N	\N	2026-01-21 03:25:50.133072	2026-01-21 03:26:00.56436	2026-01-22 03:25:50.133084	t	2	1
20	820c792f-cf34-40f0-8454-4a31cf477820	5	\N	\N	2026-01-20 23:59:55.794142	2026-01-21 00:02:27.840391	2026-01-21 23:59:55.794154	t	6	3
23	40bfbc6d-815a-4ccb-a16b-247f31645dbb	5	\N	\N	2026-01-21 03:46:56.261593	2026-01-21 03:47:25.593573	2026-01-22 03:46:56.261606	t	2	1
\.


--
-- Data for Name: user_stats; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.user_stats (id, user_id, total_queries, total_sessions, last_query_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: adk_dev_user
--

COPY public.users (id, username, email, full_name, hashed_password, google_id, auth_provider, is_active, default_agent_id, created_at, updated_at, last_login) FROM stdin;
1	testuser	test@example.com	Test User	$2b$12$6EPD3pp7v35EOl19/UEqzeUIESpFI0mhqwuuKkxuplExK3QDWGJOG	\N	local	t	\N	2026-01-18 23:53:30.515981	2026-01-18 23:53:30.515981	2026-01-20 16:34:32.47633
13	Robert_deleted_13	robert.fresh@example.com	Robert Fresh	$2b$12$NvKrmQ7D3WApMQy0wkwAs.BC76/VhmNmcDKjSjBDQR3UJlRLVAsiC	\N	local	f	\N	2026-01-19 23:45:10.516907	2026-01-20 16:40:29.180431	\N
15	test-writer	test-writer@develom.com	Test Writer	$2b$12$nT4kwCP9DpHknxmdHXhkAu/sH5a5laO.hz3jxZZr9BKcE2J7sk4Bq	\N	local	t	\N	2026-01-20 16:43:03.807977	2026-01-20 16:43:03.807977	\N
9	testuser999	test999@example.com	Test User 999	$2b$12$hmLFr02Avf0BeUIg3pMRSeEFse7uLd9LJQyDu.Z2FdYDzUYqXjRlK	\N	local	f	\N	2026-01-19 22:43:04.783395	2026-01-19 22:49:45.501142	\N
16	alice	alice@test.com	Alice Test	$2b$12$n0H/HeIziCDdy50vJR5NQeMtLY6k8j7VHDuw4htMT6WxTH6wftpZO	\N	local	t	\N	2026-01-29 00:06:43.799481	2026-01-29 00:06:43.799481	2026-01-29 00:46:16.901981
6	octavio	octavio@develom.com	Octavio Paredes	$2b$12$qhjcKsm6HAbw7UdbVl4yW.QJe/NMxAnSFois12F1ea6aGw1N28xDW	\N	local	f	\N	2026-01-19 21:49:55.816782	2026-01-19 22:57:56.322095	\N
8	testuser_1768859726	test_1768859726@example.com	Test User Profile	$2b$12$LDbWWmlzO6Tjbgw4EsRRdO2LCe7yeA0WYt9/KfI7mw5Frp/kfrfSO	\N	local	f	\N	2026-01-19 21:55:26.974049	2026-01-19 22:58:11.105036	\N
4	test_user_1768858532	testuser1768858532@example.com	Test User	$2b$12$DXObyr2kAxcO/l7S.ijUdOtQ0EQ1Jc3eLNvITN8aMKVwJuHnBdOi2	\N	local	f	\N	2026-01-19 21:35:32.154888	2026-01-19 22:59:14.166076	\N
11	mila	mila@develom.com	Mila Hughes	$2b$12$b2AacO5f1iUgAKCIjbdSB.ZCgwgEd9zONSD4I1pvrU.DT0PN2CT2e	\N	local	t	\N	2026-01-19 23:28:36.974948	2026-01-19 23:28:36.974948	\N
7	Robert_deleted_7	robert@develom.com	Robert Hughes	$2b$12$Xy0EuIDuJ11/n86A.Jr/tuMuy8ZwYpArYLoz/dWYR/GWKrEjJuuye	\N	local	f	\N	2026-01-19 21:51:05.309009	2026-01-19 22:52:30.040262	\N
10	robert_deleted_10	robert.new@example.com	Robert New	$2b$12$j7VlYR0OleH65O7EdZ.6Qur.SJOX8rljTHmX99h838b4h2FJ7DlTq	\N	local	f	\N	2026-01-19 23:11:14.898299	2026-01-19 23:38:14.137867	\N
5	hector	hector@develom.com	Hector DeJesus	$2b$12$VzvcKyxMCckMJCEZ.ch6WerLV2E/aBq2vk.AvT4UkUjcmKNhxeJea	\N	local	t	\N	2026-01-19 21:40:52.633763	2026-01-19 21:40:52.633763	2026-01-29 16:31:18.786387
\.


--
-- Name: agents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.agents_id_seq', 1, true);


--
-- Name: chat_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.chat_sessions_id_seq', 1, false);


--
-- Name: corpora_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.corpora_id_seq', 16, true);


--
-- Name: corpus_audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.corpus_audit_log_id_seq', 61, true);


--
-- Name: corpus_metadata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.corpus_metadata_id_seq', 10, true);


--
-- Name: document_access_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.document_access_log_id_seq', 179, true);


--
-- Name: group_corpus_access_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.group_corpus_access_id_seq', 44, true);


--
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.groups_id_seq', 55, true);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.roles_id_seq', 54, true);


--
-- Name: session_corpus_selections_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.session_corpus_selections_id_seq', 1, false);


--
-- Name: user_agent_access_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.user_agent_access_id_seq', 1, true);


--
-- Name: user_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.user_profiles_id_seq', 9, true);


--
-- Name: user_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.user_sessions_id_seq', 33, true);


--
-- Name: user_stats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.user_stats_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adk_dev_user
--

SELECT pg_catalog.setval('public.users_id_seq', 16, true);


--
-- Name: agents agents_name_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_name_key UNIQUE (name);


--
-- Name: agents agents_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: corpora corpora_name_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpora
    ADD CONSTRAINT corpora_name_key UNIQUE (name);


--
-- Name: corpora corpora_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpora
    ADD CONSTRAINT corpora_pkey PRIMARY KEY (id);


--
-- Name: corpus_audit_log corpus_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_audit_log
    ADD CONSTRAINT corpus_audit_log_pkey PRIMARY KEY (id);


--
-- Name: corpus_metadata corpus_metadata_corpus_id_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_metadata
    ADD CONSTRAINT corpus_metadata_corpus_id_key UNIQUE (corpus_id);


--
-- Name: corpus_metadata corpus_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_metadata
    ADD CONSTRAINT corpus_metadata_pkey PRIMARY KEY (id);


--
-- Name: document_access_log document_access_log_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.document_access_log
    ADD CONSTRAINT document_access_log_pkey PRIMARY KEY (id);


--
-- Name: group_corpora group_corpora_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_corpora
    ADD CONSTRAINT group_corpora_pkey PRIMARY KEY (group_id, corpus_id);


--
-- Name: group_corpus_access group_corpus_access_group_id_corpus_id_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_corpus_access
    ADD CONSTRAINT group_corpus_access_group_id_corpus_id_key UNIQUE (group_id, corpus_id);


--
-- Name: group_corpus_access group_corpus_access_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_corpus_access
    ADD CONSTRAINT group_corpus_access_pkey PRIMARY KEY (id);


--
-- Name: group_roles group_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_roles
    ADD CONSTRAINT group_roles_pkey PRIMARY KEY (group_id, role_id);


--
-- Name: groups groups_name_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_name_key UNIQUE (name);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: session_corpus_selections session_corpus_selections_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.session_corpus_selections
    ADD CONSTRAINT session_corpus_selections_pkey PRIMARY KEY (id);


--
-- Name: session_corpus_selections session_corpus_selections_user_id_corpus_id_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.session_corpus_selections
    ADD CONSTRAINT session_corpus_selections_user_id_corpus_id_key UNIQUE (user_id, corpus_id);


--
-- Name: user_agent_access user_agent_access_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_agent_access
    ADD CONSTRAINT user_agent_access_pkey PRIMARY KEY (id);


--
-- Name: user_agent_access user_agent_access_user_id_agent_id_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_agent_access
    ADD CONSTRAINT user_agent_access_user_id_agent_id_key UNIQUE (user_id, agent_id);


--
-- Name: user_groups user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_groups
    ADD CONSTRAINT user_groups_pkey PRIMARY KEY (user_id, group_id);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (id);


--
-- Name: user_profiles user_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_key UNIQUE (user_id);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- Name: user_sessions user_sessions_session_id_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_session_id_key UNIQUE (session_id);


--
-- Name: user_stats user_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_stats
    ADD CONSTRAINT user_stats_pkey PRIMARY KEY (id);


--
-- Name: user_stats user_stats_user_id_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_stats
    ADD CONSTRAINT user_stats_user_id_key UNIQUE (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_google_id_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_google_id_key UNIQUE (google_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_agents_active; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_agents_active ON public.agents USING btree (is_active);


--
-- Name: idx_audit_action; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_audit_action ON public.corpus_audit_log USING btree (action);


--
-- Name: idx_audit_corpus; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_audit_corpus ON public.corpus_audit_log USING btree (corpus_id);


--
-- Name: idx_audit_timestamp; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_audit_timestamp ON public.corpus_audit_log USING btree ("timestamp");


--
-- Name: idx_audit_user; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_audit_user ON public.corpus_audit_log USING btree (user_id);


--
-- Name: idx_chat_sessions_agent_id; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_chat_sessions_agent_id ON public.chat_sessions USING btree (agent_id);


--
-- Name: idx_chat_sessions_user_id; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_chat_sessions_user_id ON public.chat_sessions USING btree (user_id);


--
-- Name: idx_corpora_active; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_corpora_active ON public.corpora USING btree (is_active);


--
-- Name: idx_corpus_metadata_corpus; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_corpus_metadata_corpus ON public.corpus_metadata USING btree (corpus_id);


--
-- Name: idx_corpus_metadata_created_by; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_corpus_metadata_created_by ON public.corpus_metadata USING btree (created_by);


--
-- Name: idx_corpus_metadata_last_synced; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_corpus_metadata_last_synced ON public.corpus_metadata USING btree (last_synced_at);


--
-- Name: idx_corpus_metadata_status; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_corpus_metadata_status ON public.corpus_metadata USING btree (sync_status);


--
-- Name: idx_document_access_corpus; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_document_access_corpus ON public.document_access_log USING btree (corpus_id, accessed_at);


--
-- Name: idx_document_access_success; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_document_access_success ON public.document_access_log USING btree (success, accessed_at);


--
-- Name: idx_document_access_time; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_document_access_time ON public.document_access_log USING btree (accessed_at);


--
-- Name: idx_document_access_user; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_document_access_user ON public.document_access_log USING btree (user_id, accessed_at);


--
-- Name: idx_user_groups_group_id; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_user_groups_group_id ON public.user_groups USING btree (group_id);


--
-- Name: idx_user_groups_user_id; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_user_groups_user_id ON public.user_groups USING btree (user_id);


--
-- Name: idx_user_profiles_user_id; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_user_profiles_user_id ON public.user_profiles USING btree (user_id);


--
-- Name: idx_users_active; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_users_active ON public.users USING btree (is_active);


--
-- Name: idx_users_auth_provider; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_users_auth_provider ON public.users USING btree (auth_provider);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_google_id; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_users_google_id ON public.users USING btree (google_id);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: adk_dev_user
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: chat_sessions chat_sessions_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE SET NULL;


--
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: corpus_audit_log corpus_audit_log_corpus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_audit_log
    ADD CONSTRAINT corpus_audit_log_corpus_id_fkey FOREIGN KEY (corpus_id) REFERENCES public.corpora(id) ON DELETE CASCADE;


--
-- Name: corpus_audit_log corpus_audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_audit_log
    ADD CONSTRAINT corpus_audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: corpus_metadata corpus_metadata_corpus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_metadata
    ADD CONSTRAINT corpus_metadata_corpus_id_fkey FOREIGN KEY (corpus_id) REFERENCES public.corpora(id) ON DELETE CASCADE;


--
-- Name: corpus_metadata corpus_metadata_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_metadata
    ADD CONSTRAINT corpus_metadata_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: corpus_metadata corpus_metadata_last_synced_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.corpus_metadata
    ADD CONSTRAINT corpus_metadata_last_synced_by_fkey FOREIGN KEY (last_synced_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: document_access_log document_access_log_corpus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.document_access_log
    ADD CONSTRAINT document_access_log_corpus_id_fkey FOREIGN KEY (corpus_id) REFERENCES public.corpora(id) ON DELETE CASCADE;


--
-- Name: document_access_log document_access_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.document_access_log
    ADD CONSTRAINT document_access_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: group_corpora group_corpora_corpus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_corpora
    ADD CONSTRAINT group_corpora_corpus_id_fkey FOREIGN KEY (corpus_id) REFERENCES public.corpora(id) ON DELETE CASCADE;


--
-- Name: group_corpora group_corpora_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_corpora
    ADD CONSTRAINT group_corpora_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;


--
-- Name: group_corpus_access group_corpus_access_corpus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_corpus_access
    ADD CONSTRAINT group_corpus_access_corpus_id_fkey FOREIGN KEY (corpus_id) REFERENCES public.corpora(id) ON DELETE CASCADE;


--
-- Name: group_corpus_access group_corpus_access_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_corpus_access
    ADD CONSTRAINT group_corpus_access_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;


--
-- Name: group_roles group_roles_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_roles
    ADD CONSTRAINT group_roles_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;


--
-- Name: group_roles group_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.group_roles
    ADD CONSTRAINT group_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: session_corpus_selections session_corpus_selections_corpus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.session_corpus_selections
    ADD CONSTRAINT session_corpus_selections_corpus_id_fkey FOREIGN KEY (corpus_id) REFERENCES public.corpora(id) ON DELETE CASCADE;


--
-- Name: session_corpus_selections session_corpus_selections_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.session_corpus_selections
    ADD CONSTRAINT session_corpus_selections_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_agent_access user_agent_access_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_agent_access
    ADD CONSTRAINT user_agent_access_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE CASCADE;


--
-- Name: user_agent_access user_agent_access_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_agent_access
    ADD CONSTRAINT user_agent_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_groups user_groups_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_groups
    ADD CONSTRAINT user_groups_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;


--
-- Name: user_groups user_groups_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_groups
    ADD CONSTRAINT user_groups_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_profiles user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_sessions user_sessions_active_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_active_agent_id_fkey FOREIGN KEY (active_agent_id) REFERENCES public.agents(id);


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_stats user_stats_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adk_dev_user
--

ALTER TABLE ONLY public.user_stats
    ADD CONSTRAINT user_stats_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict QM478XTflUizLGdE70WWmQi5cof9C8NAbWDvxCxfwgx175u29gDFKy9nwE9o7ir

