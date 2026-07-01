class HealthMixin:

    def _set_health_label(self, label_widget, titulo, estado, detalhe):
        colors = {
            "ok": "#22c55e",
            "warn": "#f59e0b",
            "error": "#ef4444",
            "idle": "#94a3b8",
        }
        color = colors.get(estado, colors["idle"])
        label_widget.setText(f"● {titulo}: {detalhe}")
        label_widget.setStyleSheet(f"color: {color}; font-weight: 600;")

    def _refresh_health_panels(self):
        modo = self.config.get("modo", "automatico")
        bindings = self.config.get("gestures", {}).get("bindings", {})
        active_set = set(self._active_gestures())

        camera_running = bool(self.engine and self.engine.isRunning())
        if camera_running:
            self._set_health_label(self.health_camera, "Câmera", "ok", "Em execução")
        else:
            selected_name = self.camera_device_combo.currentText() or "Câmera"
            self._set_health_label(self.health_camera, "Câmera", "idle", f"Pronta ({selected_name})")

        if modo in ("manual", "automatico"):
            obs_status_text = self.obs_status_label.text().lower()
            if "conectado" in obs_status_text and "falha" not in obs_status_text:
                self._set_health_label(self.health_obs, "OBS", "ok", "Conectado")
            elif camera_running:
                self._set_health_label(self.health_obs, "OBS", "warn", "Aguardando conexão")
            else:
                self._set_health_label(self.health_obs, "OBS", "idle", "Não testado")
        else:
            self._set_health_label(self.health_obs, "OBS", "idle", "Desativado (modo Teste)")

        ativos = [gesture for gesture in active_set if gesture in bindings]
        if not ativos:
            self._set_health_label(self.health_gestos, "Gestos", "warn", "Nenhum gesto ativo")
        else:
            self._set_health_label(self.health_gestos, "Gestos", "ok", f"{len(ativos)} gesto(s) ativos")

    def _update_runtime_health_from_status(self, text):
        text_lower = (text or "").lower()

        if "falha ao iniciar câmera" in text_lower:
            self._set_health_label(self.health_camera, "Câmera", "error", "Falha ao iniciar")
            return

        if "câmera iniciada" in text_lower:
            self._set_health_label(self.health_camera, "Câmera", "ok", "Conectada")

        if "obs conectado" in text_lower:
            self._set_health_label(self.health_obs, "OBS", "ok", "Conectado")
        elif "falha ao conectar obs" in text_lower:
            self._set_health_label(self.health_obs, "OBS", "error", "Falha de conexão")

        if "engine parada" in text_lower:
            self._refresh_health_panels()
