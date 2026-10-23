import React, { useState } from "react";
import { Button, Form, ListGroup, Alert } from "react-bootstrap";
import LoadingBar from "./LoadingBar";
import { ErrorState } from "./AsyncState";
import apiClient, { BASE_URL, handleUnauthorized } from "../api/apiClient";
import { authHeaders } from "../utils/authStorage";
import { useAsync } from "../hooks/useAsync";
import { friendlyError } from "../utils/friendlyError";

export const DOCUMENTS_LIST_ENDPOINT = "/api/documents/list";

const fetchDocumentList = () =>
  apiClient
    .get(DOCUMENTS_LIST_ENDPOINT, {}, { quiet: true })
    .then((res) => (Array.isArray(res?.data?.files) ? res.data.files : []));

/**
 * Docs tab. When the parent passes `files` (+ `onRefresh`) it is a controlled
 * list; otherwise (how MainLayout mounts it) it loads GET /api/documents/list
 * itself and reloads after an upload or on "Refresh List".
 */
const UploadsManagerComponent = ({ files: filesProp, onUpload, onRefresh: onRefreshProp }) => {
  const controlled = filesProp !== undefined;
  const list = useAsync(fetchDocumentList, {
    immediate: !controlled,
    errorFallback: "We couldn't load your documents. Please try again.",
  });
  const files = controlled ? filesProp : list.data;
  const onRefresh = controlled ? onRefreshProp : () => list.run();
  const listLoading = !controlled && list.status === "loading";
  const listError = !controlled && list.status === "error";

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setError(null);
    setSuccess(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    setError(null);
    setSuccess(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      // Use correct backend upload endpoint from registry if available
      let uploadEndpoint = "/api/documents/upload";
      if (window.endpoints && window.endpoints.upload) {
        uploadEndpoint = window.endpoints.upload;
      }
      // Same backend as the list (apiClient base: same origin or REACT_APP_API_URL).
      const uploadUrl = /^https?:\/\//i.test(uploadEndpoint)
        ? uploadEndpoint
        : `${(BASE_URL || "").replace(/\/+$/, "")}${uploadEndpoint}`;
      // Raw fetch (multipart) bypasses apiClient: send the token ourselves.
      const res = await fetch(uploadUrl, {
        method: "POST",
        headers: authHeaders(),
        body: formData,
      });
      if (res.status === 401 && typeof handleUnauthorized === "function") {
        handleUnauthorized({ response: { status: 401 }, config: { url: uploadUrl } });
      }
      if (!res.ok) throw Object.assign(new Error("Upload failed"), { response: { status: res.status } });
      setSuccess("File uploaded successfully!");
      setSelectedFile(null);
      if (onUpload) onUpload();
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error("Upload failed:", err);
      setError(friendlyError(err, "The upload didn't finish. Please try again."));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="uploads-manager">
      <h5>Upload Document</h5>
      <Form onSubmit={handleUpload} className="mb-3">
        <Form.Group controlId="uploadFile">
          <Form.Label className="visually-hidden">Choose a document to upload</Form.Label>
          <Form.Control type="file" onChange={handleFileChange} />
        </Form.Group>
        <Button type="submit" variant="primary" disabled={uploading || !selectedFile} className="mt-2">
          {uploading ? <LoadingBar inline label="Uploading…" /> : "Upload"}
        </Button>
      </Form>
      {uploading && <LoadingBar label={`Uploading ${selectedFile?.name || "your file"}…`} className="py-3" />}
      {error && !uploading && (
        <ErrorState compact title="Upload failed" message={error} onRetry={selectedFile ? handleUpload : undefined} />
      )}
      {success && <Alert variant="success">{success}</Alert>}
      <h6 className="mt-4">Uploaded Files</h6>
      {listLoading ? (
        <LoadingBar label="Loading your documents…" slow={list.isSlow} className="py-3" />
      ) : listError ? (
        <ErrorState compact title="Couldn't load your documents" message={list.error} onRetry={list.retry} />
      ) : (
        <ListGroup>
          {files && files.length > 0 ? (
            files.map((file, idx) => (
              <ListGroup.Item key={file.filename || file.name || idx}>
                {file.filename || file.name} <span className="text-muted">({Math.round((file.size || 0) / 1024)} KB)</span>
              </ListGroup.Item>
            ))
          ) : (
            <ListGroup.Item>No files uploaded yet.</ListGroup.Item>
          )}
        </ListGroup>
      )}
      <Button variant="secondary" size="sm" className="mt-2" onClick={onRefresh} disabled={!onRefresh || listLoading}>
        Refresh List
      </Button>
    </div>
  );
};

export default UploadsManagerComponent;
