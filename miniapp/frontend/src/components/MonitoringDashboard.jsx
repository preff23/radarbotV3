import React, { useState, useEffect } from 'react';
import './MonitoringDashboard.css';

const MonitoringDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [overallStatus, setOverallStatus] = useState('unknown');
  const [components, setComponents] = useState([]);
  const [metrics, setMetrics] = useState({
    memoryUsage: 0,
    activeUsers: 0,
    cacheHitRate: 0,
    errorRate: 0
  });
  const [recentErrors, setRecentErrors] = useState([]);

  const statusConfig = {
    healthy: {
      text: 'Система работает нормально',
      description: 'Все компоненты функционируют корректно',
      icon: '✓',
      className: 'healthy'
    },
    warning: {
      text: 'Обнаружены предупреждения',
      description: 'Некоторые компоненты требуют внимания',
      icon: '⚠',
      className: 'warning'
    },
    error: {
      text: 'Критические ошибки',
      description: 'Требуется немедленное вмешательство',
      icon: '✗',
      className: 'error'
    },
    unknown: {
      text: 'Статус неизвестен',
      description: 'Не удалось получить статус системы',
      icon: '?',
      className: 'unknown'
    }
  };

  const currentStatus = statusConfig[overallStatus] || statusConfig.unknown;

  useEffect(() => {
    refreshData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refreshData, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const refreshData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchHealthStatus(),
        fetchMetrics(),
        fetchRecentErrors()
      ]);
    } catch (error) {
      console.error('Ошибка при обновлении данных:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHealthStatus = async () => {
    try {
      const response = await fetch('/api/health');
      const data = await response.json();
      
      setOverallStatus(data.status);
      setComponents(data.components || []);
    } catch (error) {
      console.error('Ошибка получения статуса:', error);
      setOverallStatus('error');
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/health/metrics');
      const data = await response.json();
      
      setMetrics({
        memoryUsage: data.memory_usage || 0,
        activeUsers: data.active_users || 0,
        cacheHitRate: data.cache_hit_rate || 0,
        errorRate: data.error_rate || 0
      });
    } catch (error) {
      console.error('Ошибка получения метрик:', error);
    }
  };

  const fetchRecentErrors = async () => {
    try {
      const response = await fetch('/api/health/errors');
      const data = await response.json();
      
      setRecentErrors(data.errors || []);
    } catch (error) {
      console.error('Ошибка получения логов:', error);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString('ru-RU');
  };

  return (
    <div className="monitoring-dashboard">
      <div className="dashboard-header">
        <h2>Системный мониторинг</h2>
        <div className="refresh-controls">
          <button 
            onClick={refreshData} 
            disabled={loading} 
            className="refresh-btn"
          >
            <span className={`icon-refresh ${loading ? 'spinning' : ''}`}>↻</span>
            Обновить
          </button>
          <div className="auto-refresh">
            <label>
              <input 
                type="checkbox" 
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              Авто-обновление (30с)
            </label>
          </div>
        </div>
      </div>

      {/* Общий статус */}
      <div className="status-overview">
        <div className={`status-card ${currentStatus.className}`}>
          <div className="status-icon">
            {currentStatus.icon}
          </div>
          <div className="status-info">
            <h3>{currentStatus.text}</h3>
            <p>{currentStatus.description}</p>
          </div>
        </div>
      </div>

      {/* Компоненты системы */}
      <div className="components-grid">
        {components.map((component, index) => (
          <div key={index} className="component-card">
            <div className="component-header">
              <h4>{component.name}</h4>
              <span className={`status-badge ${component.status}`}>
                {component.statusText}
              </span>
            </div>
            <div className="component-details">
              {component.details && (
                <div className="details">
                  {Object.entries(component.details).map(([key, value]) => (
                    <div key={key} className="detail-item">
                      <span className="detail-label">{key}:</span>
                      <span className="detail-value">{value}</span>
                    </div>
                  ))}
                </div>
              )}
              {component.error && (
                <div className="error-message">
                  <span className="icon-warning">⚠</span>
                  {component.error}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Метрики производительности */}
      <div className="metrics-section">
        <h3>Метрики производительности</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-value">{metrics.memoryUsage}%</div>
            <div className="metric-label">Использование памяти</div>
            <div className="metric-bar">
              <div 
                className="metric-fill" 
                style={{ width: `${metrics.memoryUsage}%` }}
              ></div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{metrics.activeUsers}</div>
            <div className="metric-label">Активные пользователи</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{metrics.cacheHitRate}%</div>
            <div className="metric-label">Cache Hit Rate</div>
            <div className="metric-bar">
              <div 
                className="metric-fill" 
                style={{ width: `${metrics.cacheHitRate}%` }}
              ></div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{metrics.errorRate}%</div>
            <div className="metric-label">Частота ошибок</div>
            <div className="metric-bar">
              <div 
                className="metric-fill error" 
                style={{ width: `${metrics.errorRate}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Логи ошибок */}
      {recentErrors.length > 0 && (
        <div className="logs-section">
          <h3>Последние ошибки</h3>
          <div className="logs-container">
            {recentErrors.map((error) => (
              <div key={error.id} className={`log-entry ${error.severity}`}>
                <div className="log-header">
                  <span className="log-time">{formatTime(error.timestamp)}</span>
                  <span className="log-severity">{error.severity}</span>
                </div>
                <div className="log-message">{error.message}</div>
                {error.details && (
                  <div className="log-details">
                    <pre>{error.details}</pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MonitoringDashboard;
