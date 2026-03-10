from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.templatetags.static import static


def frontend_entry(request):
    if settings.WEB_UI_MODE == "vue-dev":
        base_url = settings.VUE_DEV_SERVER_URL.rstrip("/")
        path = request.get_full_path()
        redirect_url = f"{base_url}{path}" if path != "/" else f"{base_url}/"
        return redirect(redirect_url)

    script_src = static("react/assets/index.js")
    html = f"""<!DOCTYPE html>
<html lang=\"pt-br\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>SUAP-IDEP</title>
  </head>
  <body>
    <div id=\"root\"></div>
    <script type=\"module\" src=\"{script_src}\"></script>
  </body>
</html>
"""
    return HttpResponse(html)