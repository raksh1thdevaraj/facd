/**
 * Firebase App Check Initialization (Web - reCAPTCHA Enterprise)
 * Safeguards backend APIs and Cloud Functions against scraping, abuse, and credential stuffing.
 */

import { initializeAppCheck, ReCaptchaEnterpriseProvider, AppCheck } from "firebase/app-check";
import { app } from "./firebase";

let appCheckInstance: AppCheck | null = null;

export const initAppCheck = (): AppCheck | null => {
  if (typeof window === "undefined") {
    return null;
  }

  if (appCheckInstance) {
    return appCheckInstance;
  }

  const siteKey = import.meta.env.VITE_RECAPTCHA_ENTERPRISE_SITE_KEY;

  // Local development debug mode
  if (import.meta.env.DEV) {
    // Setting debug token allows testing on localhost without triggering reCAPTCHA challenges
    // In production, debug tokens MUST NEVER be exposed.
    (self as any).FIREBASE_APPCHECK_DEBUG_TOKEN =
      import.meta.env.VITE_APPCHECK_DEBUG_TOKEN || true;
  }

  if (!siteKey) {
    console.warn(
      "[App Check] VITE_RECAPTCHA_ENTERPRISE_SITE_KEY not configured. App Check initialization deferred."
    );
    return null;
  }

  try {
    appCheckInstance = initializeAppCheck(app, {
      provider: new ReCaptchaEnterpriseProvider(siteKey),
      isTokenAutoRefreshEnabled: true,
    });
    console.info("[App Check] reCAPTCHA Enterprise provider initialized successfully.");
    return appCheckInstance;
  } catch (err) {
    console.error("[App Check] Failed to initialize reCAPTCHA Enterprise:", err);
    return null;
  }
};

export default initAppCheck;
