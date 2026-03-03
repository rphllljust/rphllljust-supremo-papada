def format_enrollment_status(status):
    labels = {
        "active": "Ativa",
        "transferred": "Transferida",
        "completed": "Concluída",
        "cancelled": "Cancelada",
    }
    return labels.get(status, status)