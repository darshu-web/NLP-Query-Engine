import React, { useState } from "react";
import DatabaseConnector from "./components/DatabaseConnector";
import DocumentUploader from "./components/DocumentUploader";
import QueryPanel from "./components/QueryPanel";
import ResultsView from "./components/ResultsView";
import { AppBar, Toolbar, Typography, Container, Grid, IconButton, Tooltip, Box, Paper, Divider } from "@mui/material";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";

function App({ colorMode, setColorMode }){
  const [results, setResults] = useState(null);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="sticky" elevation={1}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            NLP Query Engine
          </Typography>
          <Tooltip title={colorMode === "light" ? "Switch to dark" : "Switch to light"}>
            <IconButton color="inherit" onClick={() => setColorMode(colorMode === "light" ? "dark" : "light") }>
              {colorMode === "light" ? <DarkModeIcon/> : <LightModeIcon/>}
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 3, flexGrow: 1 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Database Connector</Typography>
              <DatabaseConnector />
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Document Upload</Typography>
              <DocumentUploader />
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Query</Typography>
              <QueryPanel setResults={setResults} />
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Results</Typography>
              <Divider sx={{ mb: 2 }} />
              <ResultsView results={results} />
            </Paper>
          </Grid>
        </Grid>
      </Container>

      <Box component="footer" sx={{ py: 2, textAlign: "center", opacity: 0.7 }}>
        <Typography variant="body2">© {new Date().getFullYear()} NLP Query Engine</Typography>
      </Box>
    </Box>
  );
}

export default App;
