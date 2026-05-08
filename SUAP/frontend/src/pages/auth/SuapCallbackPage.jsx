import { useEffect } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { suapApi, authApi } from "@/api/endpoints"
import toast from "react-hot-toast"

export default function SuapCallbackPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()

  useEffect(() => {
    const run = async () => {
      const status = params.get("status")
      const ticket = params.get("ticket")

      if (status !== "success" || !ticket) {
        toast.error("Falha no login SUAP.")
        navigate("/login", { replace: true })
        return
      }

      try {
        const { data } = await suapApi.exchangeTicket(ticket)
        localStorage.setItem("access_token", data.access)
        localStorage.setItem("refresh_token", data.refresh)
        await authApi.me()
        toast.success("Login com SUAP realizado com sucesso!")
        navigate("/dashboard", { replace: true })
      } catch (error) {
        toast.error("Nao foi possivel concluir o login SUAP.")
        navigate("/login", { replace: true })
      }
    }

    run()
  }, [navigate, params])

  return <div className="loading-screen"><div className="spinner" /></div>
}
