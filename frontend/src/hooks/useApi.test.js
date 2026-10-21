import { renderHook, act, waitFor } from "@testing-library/react";
import { useApi } from "./useApi";
import apiClient from "../api/apiClient";
import { AppWrapper, healthyGet } from "../test-utils";

// useApi goes through apiClient (axios), not window.fetch, and needs AppProvider.
// The old version of this file tested a fetch-based `apiCall` that no longer exists.
jest.mock("../api/apiClient");

describe("useApi Hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiClient.get.mockImplementation(healthyGet);
    jest.spyOn(console, "error").mockImplementation(() => {});
  });
  afterEach(() => console.error.mockRestore());

  test("handles successful API call", async () => {
    const mockData = { message: "Success" };
    apiClient.get.mockImplementation((url) => (url === "/api/test" ? Promise.resolve({ data: mockData }) : healthyGet(url)));

    const { result } = renderHook(() => useApi(), { wrapper: AppWrapper });

    let response;
    await act(async () => {
      response = await result.current.get("/api/test", { params: { q: "x" } });
    });

    expect(response).toEqual(mockData);
    expect(apiClient.get).toHaveBeenCalledWith("/api/test", { params: { q: "x" } });
  });

  test("handles API error", async () => {
    apiClient.get.mockImplementation((url) => (url === "/api/test"
      ? Promise.reject({ message: "Request failed with status code 500", response: { status: 500, data: { error: "API Error" } } })
      : healthyGet(url)));

    const { result } = renderHook(() => useApi(), { wrapper: AppWrapper });

    await act(async () => {
      await expect(result.current.get("/api/test")).rejects.toBeDefined();
    });
    // Backend error body wins over the generic axios message
    expect(result.current.error).toBe("API Error");
    expect(result.current.loading).toBe(false);
  });

  test("handles network error", async () => {
    apiClient.get.mockImplementation((url) => (url === "/api/test" ? Promise.reject(new Error("Network Error")) : healthyGet(url)));

    const { result } = renderHook(() => useApi(), { wrapper: AppWrapper });

    await act(async () => {
      await expect(result.current.get("/api/test")).rejects.toThrow("Network Error");
    });
    expect(result.current.error).toBe("Network Error");
  });

  test("sends POST data correctly", async () => {
    const mockData = { result: "created" };
    const postData = { name: "test" };
    apiClient.post.mockResolvedValueOnce({ data: mockData });

    const { result } = renderHook(() => useApi(), { wrapper: AppWrapper });

    let response;
    await act(async () => {
      response = await result.current.post("/api/test", postData);
    });

    expect(response).toEqual(mockData);
    expect(apiClient.post).toHaveBeenCalledWith("/api/test", postData, {});
  });

  test("reports loading while a request is pending", async () => {
    let resolve;
    apiClient.put.mockReturnValueOnce(new Promise((r) => { resolve = r; }));
    const { result } = renderHook(() => useApi(), { wrapper: AppWrapper });

    let pending;
    act(() => { pending = result.current.put("/api/thing", { a: 1 }); });
    await waitFor(() => expect(result.current.loading).toBe(true));

    await act(async () => { resolve({ data: { ok: true } }); await pending; });
    expect(result.current.loading).toBe(false);
  });
});
