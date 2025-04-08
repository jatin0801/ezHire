// src/components/Workspace/WorkspaceArea.tsx
import React, { useState, useEffect } from 'react';
import EditableText from '../common/EditableText';
import './WorkspaceArea.css';

interface SequenceStepData {
  channel?: string;
  subject_line?: string;
  timing?: string;
  message_content?: string;
}

interface SequenceSteps {
  [key: string]: SequenceStepData;
}

interface WorkspaceAreaProps {
  sequenceData?: any;
}

const WorkspaceArea: React.FC<WorkspaceAreaProps> = ({ sequenceData }) => {
  const [sequenceSteps, setSequenceSteps] = useState<SequenceSteps>({
    // "step1": {
    //   "channel": "Email",
    //   "subject_line": "Exciting Opportunity at [Company Name] - Software Engineer Role",
    //   "timing": "Send 1 day after receiving the job application",
    //   "message_content": "Hi [Candidate Name],\n\nI came across your profile on LinkedIn and was impressed by your experience in software engineering. I wanted to reach out and share an exciting opportunity at [Company Name]. We are currently looking for a talented software engineer to join our team in the fintech industry. Your skills and experience align perfectly with our requirements and we would love to discuss this opportunity with you further. If you are interested, please reply to this email with your availability for a call. Looking forward to hearing from you!\n\nBest,\n[Your Name]"
    // },
    // "step2": {
    //   "channel": "LinkedIn",
    //   "timing": "Send 3 days after initial email",
    //   "message_content": "Hi [Candidate Name],\n\nI hope this message finds you well. I wanted to follow up on my previous email regarding the software engineer role at [Company Name]. We are still very interested in your profile and would love to have a chat with you about this opportunity. If you are open to it, please let me know your availability for a call or a coffee chat. Looking forward to hearing from you!\n\nBest,\n[Your Name]"
    // },
    // "step3": {
    //   "channel": "Email",
    //   "subject_line": "Final Follow-up - Software Engineer Role at [Company Name]",
    //   "timing": "Send 1 week after initial email",
    //   "message_content": "Hi [Candidate Name],\n\nI hope you are doing well. I wanted to follow up one last time regarding the software engineer role at [Company Name]. We are still very interested in your profile and believe you would be a great fit for our team. If you are no longer interested, please let me know so I can close your application. Otherwise, we would love to have a chat with you and discuss this opportunity further. Please let me know your availability for a call or a coffee chat. Looking forward to hearing from you!\n\nBest,\n[Your Name]"
    // }
  });

  const [sequenceId, setSequenceId] = useState<number | null>(null);
  const [campaignId, setCampaignId] = useState<number | null>(null);

  // Update sequence when new sequence data arrives
  useEffect(() => {
    if (sequenceData) {
      try {
        // Check if we need to parse JSON string
        let parsedData = sequenceData;
        if (typeof sequenceData === 'string') {
          try {
            parsedData = JSON.parse(sequenceData);
          } catch (e) {
            console.error("Couldn't parse sequence data as JSON:", e);
          }
        }
        
        // sequence ID and campaign ID
        if (parsedData.sequence_id) {
          setSequenceId(parsedData.sequence_id);
        }
        
        if (parsedData.campaign_id) {
          setCampaignId(parsedData.campaign_id);
        }
        
        // step structure
        const hasSteps = Object.keys(parsedData).some(key => 
          key.startsWith('step') && typeof parsedData[key] === 'object'
        );
        
        if (hasSteps) {
          // Filter out non-step keys to avoid including metadata in steps
          const stepEntries = Object.entries(parsedData).filter(([key]) => 
            key.startsWith('step')
          );
          
          if (stepEntries.length > 0) {
            const newSteps: SequenceSteps = {};
            stepEntries.forEach(([key, value]) => {
              newSteps[key] = value as SequenceStepData;
            });
            setSequenceSteps(newSteps);
          }
        }
      } catch (error) {
        console.error('Error processing sequence data:', error);
      }
    }
  }, [sequenceData]);

  const handleStepUpdate = (stepKey: string, field: string, newContent: string) => {
    setSequenceSteps(steps => ({
      ...steps,
      [stepKey]: {
        ...steps[stepKey],
        [field]: newContent
      }
    }));
  };

  return (
    <div className="workspace-area">
      <div className="workspace-header">
        <h2>
          Sequence
          {sequenceId && <span className="sequence-id"> (ID: {sequenceId})</span>}
          {campaignId && <span className="campaign-id"> - Campaign: {campaignId}</span>}
        </h2>
      </div>
      <div className="sequence-container">
        {Object.entries(sequenceSteps).map(([stepKey, stepData]) => (
          <div key={stepKey} className="sequence-step">
            <div className="step-header">
              <span className="step-number">{stepKey.replace('step', 'Step ')}:</span>
              {stepData.channel && <span className="step-channel">{stepData.channel}</span>}
            </div>
            <div className="step-content">
              {stepData.subject_line && (
                <div className="subject-line">
                  <strong>Subject:</strong> {stepData.subject_line}
                </div>
              )}
              {stepData.timing && (
                <div className="step-timing">
                  <strong>Timing:</strong> {stepData.timing}
                </div>
              )}
              {stepData.message_content && (
                <div className="message-content">
                  <strong>Message:</strong>
                  <EditableText 
                    text={stepData.message_content} 
                    onSave={(newText) => handleStepUpdate(stepKey, 'message_content', newText)}
                  />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WorkspaceArea;