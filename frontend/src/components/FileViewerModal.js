import React, { useEffect, useState } from "react";
import { Modal, Button } from "react-bootstrap";
import apiClient from "../api/apiClient";
import LoadingBar from "./LoadingBar";
import { ErrorState } from "./AsyncState";

/**
 * Viewer for the Documents tab file list (industry-standard file-view rule:
 * clicking a file in a list opens a view of the file for inspection).
 *
 * Content comes from GET /api/documents/view/<filename>, which uses the same
 * extraction path as upload (PDF via pypdf, DOCX via python-docx, plain text
 * otherwise). Types with no extractable text return extractable=false and
 * the modal says so honestly instead of inventing content. The modal is
 * separate from chat bubbles: it never touches the message-only bubble rule.
 */
export const documentsViewEndpoint = (filename) =>
  `/api/documents/view/${encodeURIComponent(filename)}`;

const formatSize = (size) => `${Math.round((size || 0) / 1024)} KB`;

const formatModified = (modified) => {
  if (!modified) return null;
  const date = new Date(modified * 1000);
  return Number.isNaN(date.getTime()) ? null : date.toLocaleString();
};

const FileViewerModal = ({ file, onClose }) => {
  const [view, setView] = useState({ status: "idle" });

  useEffect(() => {
    if (!file) return undefined;
    let cancelled = false;
    setView({ status: "loading" });
    apiClient
      .get(documentsViewEndpoint(file.filename || file.name), {}, { quiet: true })
      .then((res) => {
        if (!cancelled) setView({ status: "done", data: res?.data || {} });
      })
      .catch(() => {
        if (!cancelled) setView({ status: "error" });
      });
    return () => {
      cancelled = true;
    };
  }, [file]);

  const filename = file?.filename || file?.name || "";
  const data = view.data || {};
  const modified = formatModified(data.modified ?? file?.modified);

  return (
    <Modal show={!!file} onHide={onClose} size="lg" centered scrollable animation={false} aria-labelledby="file-viewer-title">
      <Modal.Header closeButton>
        <Modal.Title id="file-viewer-title">{filename}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p className="text-muted">
          {data.type ? `Type: ${String(data.type).toUpperCase()} • ` : ""}
          Size: {formatSize(data.size ?? file?.size)}
          {modified ? ` • Modified: ${modified}` : ""}
        </p>
        {view.status === "loading" && <LoadingBar label={`Loading ${filename}…`} />}
        {view.status === "error" && (
          <ErrorState compact title="Couldn't load this file" message="We couldn't load this file for viewing. Please try again." />
        )}
        {view.status === "done" &&
          (data.extractable ? (
            <>
              <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{data.text}</pre>
              {data.truncated && (
                <p className="text-muted">Showing the first part of this file; the full file is larger than the viewer preview.</p>
              )}
            </>
          ) : (
            <p>Preview not available for this type. The file is still listed and stored; only its text cannot be shown here.</p>
          ))}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default FileViewerModal;
