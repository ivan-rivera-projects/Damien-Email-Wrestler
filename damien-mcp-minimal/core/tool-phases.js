/**
 * Tool Phases Configuration and Management System
 * 
 * This module defines the phases for progressive tool introduction,
 * manages the current active phase, and provides functions for
 * filtering tools based on the active phase.
 * 
 * Each phase adds new tools while retaining tools from previous phases.
 * Performance thresholds are defined for each phase to ensure stability.
 */

import { CONFIG } from '../config/claude-max-config.js';

// Configuration for tool phases with progressive rollout
export const TOOL_PHASES = {
  // Phase 1: Essential core functionality
  1: {
    name: 'Essential Core',
    description: 'Basic email functionality that makes Claude MAX work',
    tools: [
      'damien_list_emails',
      'damien_get_email_details',
      'damien_create_draft',
      'damien_send_draft',
      'damien_list_drafts'
    ],
    performance: {
      maxResponseTime: 3000, // milliseconds
      errorThreshold: 0.01, // 1% error rate maximum
      latencyTarget: 800, // milliseconds
    }
  },
  
  // Phase 2: Basic email actions
  2: {
    name: 'Basic Actions',
    description: 'Essential email management actions',
    tools: [
      'damien_trash_emails',
      'damien_label_emails',
      'damien_mark_emails',
      'damien_update_draft',
      'damien_delete_draft',
      'damien_get_draft_details',
      'damien_delete_emails_permanently'
    ],
    performance: {
      maxResponseTime: 3500, // milliseconds
      errorThreshold: 0.02, // 2% error rate maximum
      latencyTarget: 1000, // milliseconds
    }
  },
  
  // Phase 3: Thread management operations
  3: {
    name: 'Thread Management',
    description: 'Thread-level operations',
    tools: [
      'damien_list_threads',
      'damien_get_thread_details',
      'damien_modify_thread_labels',
      'damien_trash_thread',
      'damien_delete_thread_permanently'
    ],
    performance: {
      maxResponseTime: 4000, // milliseconds
      errorThreshold: 0.03, // 3% error rate maximum
      latencyTarget: 1200, // milliseconds
    }
  },
  
  // Phase 4: Rule management
  4: {
    name: 'Rule Management',
    description: 'Email automation and filtering',
    tools: [
      'damien_list_rules',
      'damien_get_rule_details',
      'damien_add_rule',
      'damien_delete_rule',
      'damien_apply_rules'
    ],
    performance: {
      maxResponseTime: 4500, // milliseconds
      errorThreshold: 0.03, // 3% error rate maximum
      latencyTarget: 1500, // milliseconds
    }
  },
  
  // Phase 5: AI intelligence
  5: {
    name: 'AI Intelligence',
    description: 'Advanced AI-powered features',
    tools: [
      'damien_ai_analyze_emails',
      'damien_ai_suggest_rules',
      'damien_ai_quick_test',
      'damien_ai_create_rule',
      'damien_ai_get_insights',
      'damien_ai_optimize_inbox',
      'damien_ai_analyze_emails_large_scale',
      'damien_ai_analyze_emails_async',
      'damien_job_get_status',
      'damien_job_get_result',
      'damien_job_cancel',
      'damien_job_list'
    ],
    performance: {
      maxResponseTime: 6000, // milliseconds
      errorThreshold: 0.05, // 5% error rate maximum
      latencyTarget: 2000, // milliseconds
    }
  },
  
  // Phase 6: Account settings
  6: {
    name: 'Account Settings',
    description: 'Complete account configuration',
    tools: [
      'damien_get_vacation_settings',
      'damien_update_vacation_settings',
      'damien_get_imap_settings',
      'damien_update_imap_settings',
      'damien_get_pop_settings',
      'damien_update_pop_settings'
    ],
    performance: {
      maxResponseTime: 3000, // milliseconds
      errorThreshold: 0.02, // 2% error rate maximum
      latencyTarget: 1000, // milliseconds
    }
  }
};

class ToolPhaseManager {
  constructor() {
    // Default to Phase 1 initially
    this._currentPhase = parseInt(process.env.DAMIEN_INITIAL_PHASE || '1', 10);
    
    // Initialize performance metrics
    this._performanceMetrics = {
      responseTimes: [],
      errors: 0,
      requests: 0,
      lastReset: Date.now()
    };
    
    // Phase change event listeners
    this._phaseChangeListeners = [];
    
    // Validate current phase
    this._validatePhase(this._currentPhase);
    
    // Performance monitoring interval (reset metrics every hour)
    this._monitoringInterval = setInterval(() => this._resetMetrics(), 3600000);
  }
  
  /**
   * Get the current active phase
   */
  get currentPhase() {
    return this._currentPhase;
  }
  
  /**
   * Set the current active phase
   */
  set currentPhase(phase) {
    const phaseNum = parseInt(phase, 10);
    this._validatePhase(phaseNum);
    
    // Only trigger events if the phase actually changed
    if (this._currentPhase !== phaseNum) {
      // Store previous phase for event handlers
      const previousPhase = this._currentPhase;
      this._currentPhase = phaseNum;
      
      // Reset performance metrics when changing phases
      this._resetMetrics();
      
      // Log phase change
      this._log(`Phase changed to ${phaseNum}: ${TOOL_PHASES[phaseNum].name}`);
      
      // Trigger phase change event for listeners
      this._triggerPhaseChangeEvent(previousPhase, phaseNum);
    }
  }
  
  /**
   * Get all tools available in the current phase
   * (includes tools from all previous phases)
   */
  getPhaseTools() {
    const tools = new Set();
    
    // Include tools from all phases up to and including the current phase
    for (let phase = 1; phase <= this._currentPhase; phase++) {
      if (TOOL_PHASES[phase]) {
        TOOL_PHASES[phase].tools.forEach(tool => tools.add(tool));
      }
    }
    
    return Array.from(tools);
  }
  
  /**
   * Check if a specific tool is available in the current phase
   */
  isToolAvailable(toolName) {
    return this.getPhaseTools().includes(toolName);
  }
  
  /**
   * Get the current phase performance threshold metrics
   */
  getCurrentPhasePerformance() {
    return TOOL_PHASES[this._currentPhase].performance;
  }
  
  /**
   * Record a tool execution for performance monitoring
   */
  recordToolExecution(toolName, responseTimeMs, hasError = false) {
    // Only record if we're monitoring this tool
    if (!this.isToolAvailable(toolName)) {
      return;
    }
    
    this._performanceMetrics.responseTimes.push(responseTimeMs);
    this._performanceMetrics.requests++;
    
    if (hasError) {
      this._performanceMetrics.errors++;
    }
    
    // Check if we've exceeded performance thresholds
    this._checkPerformanceThresholds();
  }
  
  /**
   * Get current performance metrics
   */
  getPerformanceMetrics() {
    const metrics = { ...this._performanceMetrics };
    
    // Calculate averages and error rate
    const totalRequests = metrics.requests || 1; // Avoid division by zero
    
    metrics.averageResponseTime = metrics.responseTimes.length > 0
      ? metrics.responseTimes.reduce((sum, time) => sum + time, 0) / metrics.responseTimes.length
      : 0;
      
    metrics.errorRate = metrics.errors / totalRequests;
    
    // Add phase thresholds for comparison
    metrics.thresholds = this.getCurrentPhasePerformance();
    
    return metrics;
  }
  
  /**
   * Register a listener for phase change events
   * @param {Function} listener - Callback function(previousPhase, newPhase)
   * @returns {Function} Unsubscribe function
   */
  onPhaseChange(listener) {
    if (typeof listener !== 'function') {
      throw new Error('Phase change listener must be a function');
    }
    
    this._phaseChangeListeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this._phaseChangeListeners.indexOf(listener);
      if (index !== -1) {
        this._phaseChangeListeners.splice(index, 1);
      }
    };
  }
  
  /**
   * Trigger phase change event for all listeners
   * @private
   */
  _triggerPhaseChangeEvent(previousPhase, newPhase) {
    this._phaseChangeListeners.forEach(listener => {
      try {
        listener(previousPhase, newPhase);
      } catch (error) {
        this._log('Error in phase change listener', error);
      }
    });
  }
  
  /**
   * Validate backend tools against phase configuration
   * Ensures all configured tools actually exist in the backend
   */
  async validateToolsExist(damienClient) {
    try {
      // Get all available tools from backend
      const backendTools = await damienClient.getTools();
      const backendToolNames = backendTools.map(tool => tool.name);
      
      // Check if all tools in all phases exist in the backend
      const missingTools = {};
      let allToolsExist = true;
      
      for (const [phase, config] of Object.entries(TOOL_PHASES)) {
        const missingInPhase = config.tools.filter(tool => !backendToolNames.includes(tool));
        
        if (missingInPhase.length > 0) {
          missingTools[phase] = missingInPhase;
          allToolsExist = false;
        }
      }
      
      if (!allToolsExist) {
        this._log('⚠️ Warning: Some configured tools are missing in the backend', missingTools);
      } else {
        this._log('✅ All configured tools exist in the backend');
      }
      
      return { 
        valid: allToolsExist, 
        missingTools 
      };
    } catch (error) {
      this._log('Error validating tools against backend', error);
      throw new Error(`Tool validation failed: ${error.message}`);
    }
  }
  
  /**
   * Validate that the phase is valid
   * @private
   */
  _validatePhase(phase) {
    if (!Number.isInteger(phase) || phase < 1 || phase > Object.keys(TOOL_PHASES).length) {
      throw new Error(`Invalid phase: ${phase}. Must be between 1 and ${Object.keys(TOOL_PHASES).length}`);
    }
  }
  
  /**
   * Reset performance metrics
   * @private
   */
  _resetMetrics() {
    this._performanceMetrics = {
      responseTimes: [],
      errors: 0,
      requests: 0,
      lastReset: Date.now()
    };
    
    this._log('Performance metrics reset');
  }
  
  /**
   * Check if performance thresholds have been exceeded
   * @private
   */
  _checkPerformanceThresholds() {
    // Skip if we don't have enough data
    if (this._performanceMetrics.requests < 10) {
      return;
    }
    
    const metrics = this.getPerformanceMetrics();
    const thresholds = this.getCurrentPhasePerformance();
    
    const exceededThresholds = [];
    
    if (metrics.averageResponseTime > thresholds.maxResponseTime) {
      exceededThresholds.push(`Average response time (${metrics.averageResponseTime.toFixed(2)}ms) exceeds threshold (${thresholds.maxResponseTime}ms)`);
    }
    
    if (metrics.errorRate > thresholds.errorThreshold) {
      exceededThresholds.push(`Error rate (${(metrics.errorRate * 100).toFixed(2)}%) exceeds threshold (${thresholds.errorThreshold * 100}%)`);
    }
    
    if (exceededThresholds.length > 0) {
      this._log('⚠️ Performance thresholds exceeded:', exceededThresholds);
    }
  }
  
  /**
   * Log messages (to stderr to avoid interfering with MCP communication)
   * @private
   */
  _log(message, data = null) {
    if (CONFIG.LOG_LEVEL === 'DEBUG' || CONFIG.VERBOSE_LOGGING) {
      const timestamp = new Date().toISOString();
      process.stderr.write(`[${timestamp}] ToolPhaseManager: ${message}\n`);
      
      if (data) {
        process.stderr.write(`[${timestamp}] ToolPhaseManager: ${JSON.stringify(data, null, 2)}\n`);
      }
    }
  }
  
  /**
   * Clean up resources on shutdown
   */
  shutdown() {
    clearInterval(this._monitoringInterval);
  }
}

// Create singleton instance
const phaseManager = new ToolPhaseManager();
export default phaseManager;