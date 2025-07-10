import React from "react";
import { Badge, ProgressBar } from "react-bootstrap";

const StatusBar = ({ serverConnected, userName, ragTaskStatus }) => {
  return (
    <div className="d-flex align-items-center gap-3 mb-3 flex-wrap">
      <Badge bg={serverConnected ? "success" : "danger"}>
        API: {serverConnected ? "Online" : "Offline"}
      </Badge>
      <Badge bg={userName ? "primary" : "secondary"}>
        User: {userName || "Guest"}
      </Badge>
      {ragTaskStatus && (
        <div className="d-flex align-items-center gap-2">
          <span>RAG Task:</span>
          <ProgressBar
            now={ragTaskStatus.progress}
            label={`${ragTaskStatus.progress}%`}
            style={{ minWidth: 100 }}
            variant={ragTaskStatus.progress === 100 ? "success" : "info"}
          />
        </div>
      )}
    </div>
  );
};

export default StatusBar;
