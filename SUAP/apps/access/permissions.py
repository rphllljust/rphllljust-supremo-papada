from apps.usuarios.models import PerfilUsuario


ADMIN_ONLY = (PerfilUsuario.ADMIN,)
STAFF_VIEW = (PerfilUsuario.SECRETARIA, PerfilUsuario.COORDENACAO, PerfilUsuario.ADMIN)
STAFF_MANAGE = (PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN)
TEACHING_VIEW = (PerfilUsuario.SECRETARIA, PerfilUsuario.COORDENACAO, PerfilUsuario.PROFESSOR, PerfilUsuario.ADMIN)
TEACHING_MANAGE = (PerfilUsuario.SECRETARIA, PerfilUsuario.COORDENACAO, PerfilUsuario.PROFESSOR, PerfilUsuario.ADMIN)


ACCESS_MATRIX = {
    "dashboard": {
        "web": {
            "view": TEACHING_VIEW,
        },
    },
    "cursos": {
        "web": {
            "view": STAFF_VIEW,
            "manage": STAFF_MANAGE,
        },
    },
    "turmas": {
        "web": {
            "view": TEACHING_VIEW,
            "manage": STAFF_MANAGE,
            "academic_diary": TEACHING_MANAGE,
        },
        "api": {
            "view": STAFF_VIEW,
        },
        "api_ava": {
            "export": STAFF_VIEW,
        },
    },
    "usuarios": {
        "web": {
            "view": STAFF_VIEW,
            "manage": STAFF_MANAGE,
        },
        "api": {
            "view": STAFF_VIEW,
        },
        "api_ava": {
            "export": STAFF_VIEW,
        },
    },
    "matriculas": {
        "web": {
            "view": STAFF_VIEW,
            "manage": STAFF_MANAGE,
            "documents": STAFF_VIEW,
            "document_management": STAFF_MANAGE,
            "transfers": STAFF_VIEW,
            "transfer_management": STAFF_MANAGE,
            "rules": STAFF_VIEW,
            "rule_management": STAFF_MANAGE,
            "flows": STAFF_VIEW,
            "flow_management": STAFF_MANAGE,
        },
        "api": {
            "view": STAFF_VIEW,
        },
        "api_ava": {
            "export": STAFF_VIEW,
        },
    },
    "unidades": {
        "web": {
            "view": STAFF_VIEW,
            "manage": STAFF_MANAGE,
        },
        "api": {
            "view": STAFF_VIEW,
        },
        "api_ava": {
            "export": STAFF_VIEW,
        },
    },
    "notas": {
        "web": {
            "view": TEACHING_VIEW,
            "manage": TEACHING_MANAGE,
        },
    },
    "frequencia": {
        "web": {
            "view": TEACHING_VIEW,
            "manage": TEACHING_MANAGE,
        },
    },
    "agenda": {
        "web": {
            "view": TEACHING_VIEW,
            "manage": STAFF_MANAGE,
        },
    },
    "arquivo": {
        "web": {
            "view": STAFF_VIEW,
            "manage": STAFF_MANAGE,
        },
    },
    "auditoria": {
        "web": {
            "view": STAFF_VIEW,
            "manage": ADMIN_ONLY,
        },
    },
    "documentos": {
        "web": {
            "view": STAFF_VIEW,
            "manage": STAFF_MANAGE,
        },
    },
    "estagio": {
        "web": {
            "view": TEACHING_VIEW,
            "manage": STAFF_MANAGE,
        },
    },
    "inscricoes": {
        "web": {
            "view": STAFF_VIEW,
            "manage": STAFF_MANAGE,
        },
    },
    "processos": {
        "web": {
            "view": STAFF_VIEW,
            "manage": STAFF_MANAGE,
        },
    },
    "integracao_moodle": {
        "api_ava": {
            "export": STAFF_VIEW,
        },
    },
}

AVA_EXPORT_PROFILES = (
    PerfilUsuario.SECRETARIA,
    PerfilUsuario.COORDENACAO,
    PerfilUsuario.ADMIN,
)

OBJECT_OWNER_FIELDS = ("usuario", "user", "owner", "created_by", "professor")
OBJECT_OWNER_ID_FIELDS = ("usuario_id", "user_id", "owner_id", "created_by_id", "professor_id")
