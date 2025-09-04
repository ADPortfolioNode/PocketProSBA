import React, { useState, useEffect } from 'react';
import { Accordion, Card, Button, Badge } from 'react-bootstrap';

const AccordionSubnav = ({ activeTab, onSectionChange, contentData }) => {
  const [activeKey, setActiveKey] = useState('0');

  // Dynamic subnav content based on active tab
  const getSubnavItems = () => {
    switch (activeTab) {
      case 'chat':
        return [
          {
            title: 'Conversation History',
            items: ['Recent Chats', 'Saved Sessions', 'Export History'],
            icon: '💬'
          },
          {
            title: 'Chat Settings',
            items: ['Response Style', 'Language', 'Notifications'],
            icon: '⚙️'
          },
          {
            title: 'SBA Resources',
            items: ['Quick Links', 'Help Topics', 'FAQ'],
            icon: '📚'
          }
        ];
      case 'browse':
        return [
          {
            title: 'Content Types',
            items: ['Articles', 'Blog Posts', 'Courses', 'Events'],
            icon: '📄'
          },
          {
            title: 'Filters',
            items: ['By Date', 'By Category', 'By Author'],
            icon: '🔍'
          },
          {
            title: 'Saved Items',
            items: ['Bookmarks', 'Recent Views', 'Downloads'],
            icon: '⭐'
          }
        ];
      case 'rag':
        return [
          {
            title: 'Document Management',
            items: ['Upload', 'Process', 'Index Status'],
            icon: '📁'
          },
          {
            title: 'Query Builder',
            items: ['Advanced Search', 'Filters', 'Templates'],
            icon: '🔧'
          },
          {
            title: 'Results',
            items: ['View Results', 'Export', 'Share'],
            icon: '📊'
          }
        ];
      case 'documents':
        return [
          {
            title: 'Document Center',
            items: ['My Documents', 'Shared', 'Recent'],
            icon: '📋'
          },
          {
            title: 'Upload & Process',
            items: ['Upload Files', 'Batch Process', 'Status'],
            icon: '⬆️'
          },
          {
            title: 'Organization',
            items: ['Folders', 'Tags', 'Search'],
            icon: '🏷️'
          }
        ];
      case 'sba':
        return [
          {
            title: 'SBA Programs',
            items: ['7(a) Loans', '8(a) Program', 'Microloans'],
            icon: '🏢'
          },
          {
            title: 'Resources',
            items: ['Guides', 'Templates', 'Calculators'],
            icon: '📈'
          },
          {
            title: 'Support',
            items: ['Contact', 'Training', 'Events'],
            icon: '🤝'
          }
        ];
      default:
        return [];
    }
  };

  const subnavItems = getSubnavItems();

  const handleSectionClick = (sectionTitle, item) => {
    onSectionChange && onSectionChange(sectionTitle, item);
  };

  return (
    <div className="accordion-subnav tron-accordion">
      <Accordion activeKey={activeKey} onSelect={setActiveKey}>
        {subnavItems.map((section, index) => (
          <Accordion.Item
            key={index}
            eventKey={index.toString()}
            className="tron-accordion-item"
          >
            <Accordion.Header className="tron-accordion-header">
              <span className="section-icon">{section.icon}</span>
              <span className="section-title">{section.title}</span>
              <Badge bg="primary" className="item-count">
                {section.items.length}
              </Badge>
            </Accordion.Header>
            <Accordion.Body className="tron-accordion-body">
              <div className="subnav-items">
                {section.items.map((item, itemIndex) => (
                  <Button
                    key={itemIndex}
                    variant="link"
                    className="subnav-item tron-subnav-link"
                    onClick={() => handleSectionClick(section.title, item)}
                  >
                    <span className="item-text">{item}</span>
                    <span className="item-arrow">→</span>
                  </Button>
                ))}
              </div>
            </Accordion.Body>
          </Accordion.Item>
        ))}
      </Accordion>
    </div>
  );
};

export default AccordionSubnav;
