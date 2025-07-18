import React, { useState } from "react";
import { Button, Form, ListGroup, Alert } from "react-bootstrap";
// import removed: UploadsManager from "./components/uploads/UploadsManager";

const UploadsManagerComponent = ({ files, onUpload, onRefresh }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setError(null);
    setSuccess(null);
  };
  /////upload this file to git

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
      const res = await fetch(uploadEndpoint, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      setSuccess("File uploaded successfully!");
      setSelectedFile(null);
      if (onUpload) onUpload();
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="uploads-manager">
      <h5>Upload Document</h5>
      <Form onSubmit={handleUpload} className="mb-3">
        <Form.Group controlId="uploadFile">
          <Form.Control type="file" onChange={handleFileChange} />
        </Form.Group>
        <Button type="submit" variant="primary" disabled={uploading || !selectedFile} className="mt-2">
          {uploading ? "Uploading..." : "Upload"}
        </Button>
      </Form>
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
      <h6 className="mt-4">Uploaded Files</h6>
      <ListGroup>
        {files && files.length > 0 ? (
          files.map((file, idx) => (
            <ListGroup.Item key={idx}>
              {file.filename} <span className="text-muted">({Math.round(file.size/1024)} KB)</span>
            </ListGroup.Item>
          ))
        ) : (
          <ListGroup.Item>No files uploaded yet.</ListGroup.Item>
        )}
      </ListGroup>
      <Button variant="secondary" size="sm" className="mt-2" onClick={onRefresh}>
        Refresh List
      </Button>
    </div>
  );
};

export default UploadsManagerComponent;
