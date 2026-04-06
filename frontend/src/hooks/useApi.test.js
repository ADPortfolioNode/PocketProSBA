import { renderHook, act } from "@testing-library/react";
import { useApi } from "./useApi";

// Mock fetch globally
global.fetch = jest.fn();

describe("useApi Hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("handles successful API call", async () => {
    const mockData = { message: "Success" };
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData)
    });

    const { result } = renderHook(() => useApi());

    let response;
    await act(async () => {
      response = await result.current.apiCall("/api/test", {
        method: "GET"
      });
    });

    expect(response).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith("/api/test", {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    });
  });

  test("handles API error", async () => {
    const errorMessage = "API Error";
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error"
    });

    const { result } = renderHook(() => useApi());

    await expect(async () => {
      await act(async () => {
        await result.current.apiCall("/api/test");
      });
    }).rejects.toThrow("API Error: 500 Internal Server Error");
  });

  test("handles network error", async () => {
    global.fetch.mockRejectedValueOnce(new Error("Network Error"));

    const { result } = renderHook(() => useApi());

    await expect(async () => {
      await act(async () => {
        await result.current.apiCall("/api/test");
      });
    }).rejects.toThrow("Network Error");
  });

  test("sends POST data correctly", async () => {
    const mockData = { result: "created" };
    const postData = { name: "test" };
    
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData)
    });

    const { result } = renderHook(() => useApi());

    let response;
    await act(async () => {
      response = await result.current.apiCall("/api/test", {
        method: "POST",
        body: postData
      });
    });

    expect(response).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith("/api/test", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(postData)
    });
  });
});
