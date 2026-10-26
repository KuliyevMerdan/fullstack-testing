"use client";

import { useEffect } from "react";

type TelegramWebApp = {
  initData: string;
  colorScheme: "light" | "dark";
  ready: () => void;
  expand: () => void;
  onEvent: (event: "themeChanged", handler: () => void) => void;
  offEvent: (event: "themeChanged", handler: () => void) => void;
};

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

export function TelegramInit() {
  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    if (!webApp || !webApp.initData) return;

    const applyColorScheme = () => {
      document.documentElement.style.colorScheme = webApp.colorScheme;
    };
    applyColorScheme();
    webApp.onEvent("themeChanged", applyColorScheme);
    webApp.ready();
    webApp.expand();
    return () => webApp.offEvent("themeChanged", applyColorScheme);
  }, []);

  return null;
}
