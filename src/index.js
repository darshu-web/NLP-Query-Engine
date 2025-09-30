import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import { useMemo, useState } from "react";

function ThemedApp(){
  const [mode, setMode] = useState("light");
  const theme = useMemo(()=>createTheme({
    palette: { mode,
      primary: { main: mode === "light" ? "#1f7a8c" : "#80cbc4" },
      secondary: { main: mode === "light" ? "#ff6f61" : "#ffab91" }
    },
    shape: { borderRadius: 10 },
    components: {
      MuiButton: { styleOverrides: { root: { textTransform: "none" } } }
    }
  }), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App colorMode={mode} setColorMode={setMode} />
    </ThemeProvider>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<ThemedApp />);
