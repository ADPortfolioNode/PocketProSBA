import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import App from "./App";
import apiClient from "./api/apiClient";
import { healthyGet } from "./test-utils";

jest.mock("./api/apiClient");

describe("App Component", () => {
  beforeEach(() => {
    apiClient.get.mockImplementation(healthyGet);
    window.history.pushState({}, "", "/");
  });

  test("renders without crashing", async () => {
    render(<App />);
    expect(screen.getByRole("link", { name: /PocketPro SBA home/i })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: /Funding guidance built for small business/i })).toBeInTheDocument();
  });
});
