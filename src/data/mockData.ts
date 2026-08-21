export interface FeedbackItem {
  id: string;
  author: string;
  avatar: string;
  source: 'App Store' | 'Play Store' | 'Intercom' | 'Zendesk' | 'Email' | 'User Interview';
  rating: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  category: 'UX/UI' | 'Performance' | 'Billing' | 'Feature Request' | 'Bug';
  content: string;
  timestamp: string;
  urgency: 'High' | 'Medium' | 'Low';
  aiSummary: string;
  tags: string[];
}

export interface TranscriptLine {
  id: number;
  timestamp: string;
  speaker: string;
  role: 'Customer' | 'Support Agent' | 'Product Manager';
  text: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  keywords: string[];
}

export interface AudioSession {
  id: string;
  title: string;
  customerName: string;
  company: string;
  duration: string;
  date: string;
  overallSentiment: 'positive' | 'neutral' | 'negative';
  csatScore: number;
  transcripts: TranscriptLine[];
  aiActionItems: string[];
  keyTopics: string[];
}

export interface TopicClusterData {
  id: string;
  name: string;
  mentionCount: number;
  sentimentBreakdown: { positive: number; neutral: number; negative: number };
  growthTrend: string;
  urgency: 'Critical' | 'Moderate' | 'Low';
  sampleQuotes: string[];
}

export const MOCK_FEEDBACKS: FeedbackItem[] = [
  {
    id: 'fb-101',
    author: 'Sarah Jenkins',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150',
    source: 'Intercom',
    rating: 5,
    sentiment: 'positive',
    category: 'Feature Request',
    content: 'The new AI transcription speed is blazingly fast! Saved our product team 4 hours per user testing cycle. Would love an option to export as PDF summaries.',
    timestamp: '10 mins ago',
    urgency: 'Low',
    aiSummary: 'Praised AI transcription speed, requested PDF export functionality.',
    tags: ['Speed', 'AI Transcription', 'PDF Export']
  },
  {
    id: 'fb-102',
    author: 'David Chen',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
    source: 'App Store',
    rating: 2,
    sentiment: 'negative',
    category: 'Performance',
    content: 'Audio upload frequently fails when uploading files over 50MB on mobile browser. Needs retry mechanisms or chunked upload.',
    timestamp: '45 mins ago',
    urgency: 'High',
    aiSummary: 'Mobile audio upload timeouts for files > 50MB.',
    tags: ['Mobile Upload', 'Timeout Bug', 'File Size']
  },
  {
    id: 'fb-103',
    author: 'Elena Rostova',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
    source: 'Zendesk',
    rating: 4,
    sentiment: 'positive',
    category: 'UX/UI',
    content: 'Dark mode aesthetics are stunning. The sentiment timeline during call replays makes finding key objections super effortless.',
    timestamp: '2 hours ago',
    urgency: 'Low',
    aiSummary: 'High satisfaction with dark theme UI & transcript sentiment timeline.',
    tags: ['Dark Theme', 'Transcript Timeline', 'UI']
  },
  {
    id: 'fb-104',
    author: 'Marcus Vance',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150',
    source: 'Play Store',
    rating: 3,
    sentiment: 'neutral',
    category: 'Billing',
    content: 'The product is great, but invoice generation is delayed by 24 hours after plan upgrades. Clearer billing notifications would help.',
    timestamp: '4 hours ago',
    urgency: 'Medium',
    aiSummary: 'Requested faster automated invoice receipt delivery post plan upgrade.',
    tags: ['Billing Receipts', 'Notifications']
  },
  {
    id: 'fb-105',
    author: 'Anita Roy',
    avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150',
    source: 'User Interview',
    rating: 5,
    sentiment: 'positive',
    category: 'Feature Request',
    content: 'Integrating EchoInsight with Slack for live alerts when negative feedback arrives was a game changer for our CS lead.',
    timestamp: 'Yesterday',
    urgency: 'Low',
    aiSummary: 'Appreciates Slack alert integration for real-time negative feedback routing.',
    tags: ['Slack Integration', 'CS Automation']
  }
];

export const MOCK_AUDIO_SESSION: AudioSession = {
  id: 'session-882',
  title: 'Customer Discovery - Enterprise Onboarding Call',
  customerName: 'Michael Sterling',
  company: 'Apex Digital Inc.',
  duration: '14m 32s',
  date: 'Aug 21, 2026',
  overallSentiment: 'positive',
  csatScore: 9.2,
  transcripts: [
    {
      id: 1,
      timestamp: '00:15',
      speaker: 'Alex (PM)',
      role: 'Product Manager',
      text: "Hi Michael, thanks for joining! Let's talk about your team's workflow during customer feedback analysis.",
      sentiment: 'neutral',
      keywords: ['Workflow', 'Customer Feedback']
    },
    {
      id: 2,
      timestamp: '01:05',
      speaker: 'Michael Sterling',
      role: 'Customer',
      text: "Honestly, we used to spend 15 hours a week manually listening to sales calls to find why users churned.",
      sentiment: 'negative',
      keywords: ['Manual Work', 'Churn Reason', 'Time Loss']
    },
    {
      id: 3,
      timestamp: '03:40',
      speaker: 'Michael Sterling',
      role: 'Customer',
      text: "With EchoInsight's real-time speaker diarization and sentiment breakdown, our product team immediately spotted the pricing friction point!",
      sentiment: 'positive',
      keywords: ['Diarization', 'Pricing Friction', 'Speed']
    },
    {
      id: 4,
      timestamp: '06:12',
      speaker: 'Alex (PM)',
      role: 'Product Manager',
      text: "That's fantastic to hear. Is there any specific feature request your team is missing right now?",
      sentiment: 'neutral',
      keywords: ['Feature Request']
    },
    {
      id: 5,
      timestamp: '07:25',
      speaker: 'Michael Sterling',
      role: 'Customer',
      text: "We'd love automated bi-weekly PDF report generation sent directly to our VP of Product.",
      sentiment: 'positive',
      keywords: ['Automated Reports', 'PDF Summary', 'Executive View']
    }
  ],
  aiActionItems: [
    'Add PDF automated report export option to subscription dashboard',
    'Follow up with Michael regarding API rate limits for audio transcript processing',
    'Share pricing friction insight with Product Marketing team'
  ],
  keyTopics: ['Pricing Friction', 'Automated PDF Export', 'Diarization', 'Time Savings']
};

export const MOCK_TOPIC_CLUSTERS: TopicClusterData[] = [
  {
    id: 'tc-1',
    name: 'Audio Upload Timeouts (>50MB)',
    mentionCount: 142,
    sentimentBreakdown: { positive: 5, neutral: 15, negative: 80 },
    growthTrend: '+34% this week',
    urgency: 'Critical',
    sampleQuotes: [
      'Upload failed at 98% when uploading 60MB MP3 recording.',
      'Mobile web app times out on cellular connections.'
    ]
  },
  {
    id: 'tc-2',
    name: 'Automated Executive PDF Reports',
    mentionCount: 98,
    sentimentBreakdown: { positive: 70, neutral: 25, negative: 5 },
    growthTrend: '+18% this week',
    urgency: 'Moderate',
    sampleQuotes: [
      'Need weekly summary PDFs sent to Slack and Email for leadership.',
      'Exporting charts directly into presentation format.'
    ]
  },
  {
    id: 'tc-3',
    name: 'Slack / Teams Alert Integration',
    mentionCount: 86,
    sentimentBreakdown: { positive: 85, neutral: 12, negative: 3 },
    growthTrend: '+25% this week',
    urgency: 'Low',
    sampleQuotes: [
      'Love the Slack notification bot for negative customer tickets!',
      'Can we add MS Teams webhook support?'
    ]
  },
  {
    id: 'tc-4',
    name: 'Dark Mode Contrast & Typography',
    mentionCount: 64,
    sentimentBreakdown: { positive: 90, neutral: 10, negative: 0 },
    growthTrend: '+8% this week',
    urgency: 'Low',
    sampleQuotes: [
      'The neon accent theme is very easy on the eyes.',
      'Sleek visual player makes call review enjoyable.'
    ]
  }
];

export const SENTIMENT_TREND_DATA = [
  { day: 'Mon', positive: 65, neutral: 20, negative: 15 },
  { day: 'Tue', positive: 70, neutral: 18, negative: 12 },
  { day: 'Wed', positive: 62, neutral: 22, negative: 16 },
  { day: 'Thu', positive: 78, neutral: 15, negative: 7 },
  { day: 'Fri', positive: 84, neutral: 10, negative: 6 },
  { day: 'Sat', positive: 79, neutral: 14, negative: 7 },
  { day: 'Sun', positive: 88, neutral: 8, negative: 4 }
];
