import React, { useState } from 'react';
import { sbaPrograms, businessLifecycleStages, localResourceTypes } from '../sbaResources';

const SBANavigation = ({ onProgramSelect, onResourceSelect }) => {
  const [activeTab, setActiveTab] = useState('programs');
  
  return (
    <div className="sba-navigation">
      <div className="navigation-tabs">
        <button 
          className={`nav-tab ${activeTab === 'programs' ? 'active' : ''}`}
          onClick={() => setActiveTab('programs')}
        >
          SBA Programs
        </button>
        <button 
          className={`nav-tab ${activeTab === 'lifecycle' ? 'active' : ''}`}
          onClick={() => setActiveTab('lifecycle')}
        >
          Business Lifecycle
        </button>
        <button 
          className={`nav-tab ${activeTab === 'local' ? 'active' : ''}`}
          onClick={() => setActiveTab('local')}
        >
          Local Resources
        </button>
      </div>
      
      <div className="navigation-content">
        {activeTab === 'programs' && (
          <div className="programs-grid">
            {sbaPrograms.map(program => (
              <div 
                key={program.id}
                className="program-card" 
                onClick={() => onProgramSelect(program.id)}
              >
                <div className="program-icon">{program.icon}</div>
                <div className="program-content">
                  <h3>{program.name}</h3>
                  <p>{program.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {activeTab === 'lifecycle' && (
          <div className="lifecycle-stages">
            {businessLifecycleStages.map(stage => (
              <div key={stage.id} className="lifecycle-stage">
                <h3>{stage.name}</h3>
                <p>{stage.description}</p>
                <div className="stage-resources">
                  {stage.resources.map((resource, index) => (
                    <a 
                      key={index}
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="resource-link"
                      onClick={(e) => {
                        e.preventDefault();
                        onResourceSelect({
                          title: resource.title,
                          url: resource.url,
                          stage: stage.name
                        });
                      }}
                    >
                      {resource.title}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {activeTab === 'local' && (
          <div className="local-resources">
            <p className="local-intro">
              The SBA works with a number of local partners to counsel, mentor, and train small businesses.
            </p>
            <div className="resource-types">
              {localResourceTypes.map(resource => (
                <div key={resource.id} className="resource-type">
                  <h3>{resource.name}</h3>
                  <p>{resource.description}</p>
                  <a 
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="find-local-button"
                  >
                    Find Nearby
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SBANavigation;
