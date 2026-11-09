/**
 * file: src/main.tsx
 * importable: nothing, index.html loads this file
 *
 * description: Starts the admin panel in the browser.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../../site/src/styles/site.css";
import "./panel.css";
import { App } from "./App";
import { applySavedTheme } from "./theme";

applySavedTheme();
createRoot(document.getElementById("app")!).render(<StrictMode><App /></StrictMode>);
