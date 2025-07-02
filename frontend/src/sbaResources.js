// SBA Program data and descriptions
export const sbaPrograms = [
  {
    id: 'loans',
    name: 'SBA Loans',
    description: 'Small business loan programs with competitive terms',
    icon: '💰',
    detailedDescription: `
      The SBA offers a variety of loan programs designed to meet the financing needs of small businesses. 
      These include 7(a) loans (the SBA's primary lending program), 504 loans (for major fixed assets), 
      microloans (for small amounts), and disaster loans (for businesses affected by declared disasters).
    `,
    url: 'https://www.sba.gov/funding-programs/loans'
  },
  {
    id: 'contracting',
    name: 'Government Contracting',
    description: 'Help small businesses win federal contracts',
    icon: '📝',
    detailedDescription: `
      The federal government aims to award at least 23% of all federal contracting dollars to small businesses.
      The SBA offers certification programs such as 8(a) Business Development, HUBZone, Women-Owned Small Business (WOSB),
      and Service-Disabled Veteran-Owned Small Business (SDVOSB) to help small businesses compete for contracts.
    `,
    url: 'https://www.sba.gov/federal-contracting'
  },
  {
    id: 'disaster',
    name: 'Disaster Assistance',
    description: 'Loans for businesses affected by disasters',
    icon: '🚨',
    detailedDescription: `
      The SBA provides low-interest disaster loans to businesses of all sizes, private non-profit organizations, 
      homeowners, and renters. These loans can be used to repair or replace real estate, personal property, 
      machinery and equipment, and inventory and business assets that have been damaged or destroyed in a declared disaster.
    `,
    url: 'https://www.sba.gov/funding-programs/disaster-assistance'
  },
  {
    id: 'counseling',
    name: 'Counseling & Training',
    description: 'Free business counseling and training programs',
    icon: '👥',
    detailedDescription: `
      The SBA offers free business counseling and training through partners like Small Business Development Centers (SBDCs),
      SCORE (Service Corps of Retired Executives), Women's Business Centers (WBCs), and Veterans Business Outreach Centers (VBOCs).
      These resources provide mentoring, business plan development, marketing assistance, and much more.
    `,
    url: 'https://www.sba.gov/local-assistance'
  },
  {
    id: 'international',
    name: 'International Trade',
    description: 'Export assistance and financing programs',
    icon: '🌎',
    detailedDescription: `
      The SBA offers export loans, international trade loans, and export express programs to help small businesses 
      enter and succeed in international markets. These programs provide capital to finance the production of goods 
      or services for export, as well as to support expansion into new markets.
    `,
    url: 'https://www.sba.gov/business-guide/grow-your-business/export-products'
  },
  {
    id: 'innovation',
    name: 'SBIR/STTR',
    description: 'Research and development grants for innovation',
    icon: '💡',
    detailedDescription: `
      The Small Business Innovation Research (SBIR) and Small Business Technology Transfer (STTR) programs 
      are competitive grant programs that encourage small businesses to engage in Federal Research/Research and Development 
      with the potential for commercialization. These programs help small businesses compete for federal R&D awards.
    `,
    url: 'https://www.sbir.gov/'
  },
  {
    id: 'opportunities',
    name: 'Opportunities for Veterans',
    description: 'Resources and programs for veteran entrepreneurs',
    icon: '🎖️',
    detailedDescription: `
      The SBA offers resources specifically for veterans, service-disabled veterans, reserve component members, 
      and their spouses. These include business training, counseling, access to capital programs, and government 
      contracting opportunities to help them start, grow, and expand their businesses.
    `,
    url: 'https://www.sba.gov/business-guide/grow-your-business/veteran-owned-businesses'
  },
  {
    id: 'women',
    name: 'Women-Owned Businesses',
    description: 'Support for women entrepreneurs',
    icon: '👩‍💼',
    detailedDescription: `
      The SBA supports women entrepreneurs through Women's Business Centers (WBCs), which provide business training, 
      counseling, and other resources. The SBA also offers the Women-Owned Small Business (WOSB) Federal Contracting Program 
      to help women-owned small businesses compete for federal contracts.
    `,
    url: 'https://www.sba.gov/business-guide/grow-your-business/women-owned-businesses'
  }
];

// SBA Business Lifecycle stages and related resources
export const businessLifecycleStages = [
  {
    id: 'plan',
    name: 'Plan Your Business',
    description: 'Resources for business planning and research',
    resources: [
      { title: 'Business Plan Guide', url: 'https://www.sba.gov/business-guide/plan-your-business/write-your-business-plan' },
      { title: 'Market Research', url: 'https://www.sba.gov/business-guide/plan-your-business/market-research-competitive-analysis' },
      { title: 'Calculate Startup Costs', url: 'https://www.sba.gov/business-guide/plan-your-business/calculate-your-startup-costs' }
    ]
  },
  {
    id: 'launch',
    name: 'Launch Your Business',
    description: 'Steps to legally start and structure your business',
    resources: [
      { title: 'Choose a Business Structure', url: 'https://www.sba.gov/business-guide/launch-your-business/choose-business-structure' },
      { title: 'Register Your Business', url: 'https://www.sba.gov/business-guide/launch-your-business/register-your-business' },
      { title: 'Get Federal & State Tax IDs', url: 'https://www.sba.gov/business-guide/launch-your-business/get-federal-state-tax-id-numbers' }
    ]
  },
  {
    id: 'manage',
    name: 'Manage Your Business',
    description: 'Day-to-day operations and compliance guidance',
    resources: [
      { title: 'Business Finances', url: 'https://www.sba.gov/business-guide/manage-your-business/manage-your-finances' },
      { title: 'Hire & Retain Employees', url: 'https://www.sba.gov/business-guide/manage-your-business/hire-manage-employees' },
      { title: 'Business Insurance', url: 'https://www.sba.gov/business-guide/manage-your-business/get-business-insurance' }
    ]
  },
  {
    id: 'grow',
    name: 'Grow Your Business',
    description: 'Strategies and resources for business expansion',
    resources: [
      { title: 'Access Additional Funding', url: 'https://www.sba.gov/business-guide/grow-your-business/get-more-funding' },
      { title: 'Marketing and Sales', url: 'https://www.sba.gov/business-guide/manage-your-business/marketing-sales' },
      { title: 'Expand to New Locations', url: 'https://www.sba.gov/business-guide/grow-your-business/open-new-location' }
    ]
  }
];

// SBA local resource types
export const localResourceTypes = [
  {
    id: 'sbdc',
    name: 'Small Business Development Centers',
    description: 'Local centers that provide counseling and training to small business owners',
    url: 'https://www.sba.gov/local-assistance/find/?type=Small%20Business%20Development%20Center&pageNumber=1'
  },
  {
    id: 'score',
    name: 'SCORE Business Mentors',
    description: 'Volunteer business counselors providing free business advice',
    url: 'https://www.score.org/find-mentor'
  },
  {
    id: 'wbc',
    name: 'Women\'s Business Centers',
    description: 'Centers providing business training and counseling for women entrepreneurs',
    url: 'https://www.sba.gov/local-assistance/find/?type=Women%27s%20Business%20Center&pageNumber=1'
  },
  {
    id: 'vboc',
    name: 'Veterans Business Outreach Centers',
    description: 'Centers providing business training and counseling for veteran entrepreneurs',
    url: 'https://www.sba.gov/local-assistance/find/?type=Veterans%20Business%20Outreach%20Center&pageNumber=1'
  },
  {
    id: 'district',
    name: 'SBA District Offices',
    description: 'Local SBA offices providing assistance to small businesses',
    url: 'https://www.sba.gov/local-assistance/find/?type=SBA%20District%20Office&pageNumber=1'
  }
];

// Common business questions and their RAG queries
export const commonBusinessQuestions = [
  {
    question: "How do I qualify for an SBA loan?",
    query: "What are the requirements and qualifications for SBA loan programs?"
  },
  {
    question: "What business structure should I choose?",
    query: "What are the differences between LLC, S-Corp, C-Corp, and Sole Proprietorship structures?"
  },
  {
    question: "How can I get government contracts?",
    query: "What are the steps to qualify for government contracting opportunities as a small business?"
  },
  {
    question: "What resources are available for women business owners?",
    query: "What SBA programs and resources are specifically available for women-owned businesses?"
  },
  {
    question: "How do I write a business plan?",
    query: "What are the essential components of a strong small business plan according to SBA guidelines?"
  },
  {
    question: "What disaster assistance is available for my business?",
    query: "What types of SBA disaster loans and assistance are available for businesses affected by disasters?"
  },
  {
    question: "How can I find local business assistance?",
    query: "How do I connect with local SBA resource partners and assistance programs in my area?"
  },
  {
    question: "What tax benefits are available for small businesses?",
    query: "What tax deductions, credits, and benefits are available specifically for small businesses?"
  }
];

// SBA learning center topics
export const learningCenterTopics = [
  {
    id: 'financing',
    name: 'Financing Your Business',
    courses: [
      'Understanding SBA Loan Options',
      'Preparing a Loan Application',
      'Alternative Funding Sources',
      'Managing Business Credit'
    ]
  },
  {
    id: 'marketing',
    name: 'Marketing & Sales',
    courses: [
      'Digital Marketing Basics',
      'Social Media for Small Business',
      'Customer Acquisition Strategies',
      'Building a Marketing Plan'
    ]
  },
  {
    id: 'operations',
    name: 'Business Operations',
    courses: [
      'Supply Chain Management',
      'Inventory Control Systems',
      'Business Process Optimization',
      'Risk Management'
    ]
  },
  {
    id: 'legal',
    name: 'Legal & Compliance',
    courses: [
      'Business Structure Selection',
      'Intellectual Property Protection',
      'Employment Law Basics',
      'Tax Compliance for Small Business'
    ]
  }
];
