from apps.usuarios.forms import TipoUsuarioForm
from apps.usuarios.models import PerfilUsuario


class ProfessorForm(TipoUsuarioForm):
    tipo_valor = PerfilUsuario.PROFESSOR
