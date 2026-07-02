import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import AppLayout from "./components/Layout";
import OverviewPage from "./pages/OverviewPage";
import DistributionPage from "./pages/DistributionPage";
import PipelinePage from "./pages/PipelinePage";
import EpisodesPage from "./pages/EpisodesPage";
import StoragePage from "./pages/StoragePage";
import "antd/dist/reset.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/distribution" element={<DistributionPage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/episodes" element={<EpisodesPage />} />
            <Route path="/storage" element={<StoragePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  </React.StrictMode>
);
