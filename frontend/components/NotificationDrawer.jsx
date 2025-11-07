import React, { useState, useEffect } from 'react';
import './NotificationDrawer.css';

const NotificationDrawer = ({ isOpen, onClose }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [activeTab, setActiveTab] = useState('all'); // all, unread, messages, system

  useEffect(() => {
    if (isOpen) {
      loadNotifications();
      connectToNotifications();
    }
  }, [isOpen]);

  const loadNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/notifications/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications);
        setUnreadCount(data.notifications.filter(n => !n.is_read).length);
      }
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const connectToNotifications = () => {
    // SSE connection for real-time notifications
    const token = localStorage.getItem('token');
    const eventSource = new EventSource(`/api/sse/notifications?token=${token}`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'notification') {
        // Add new notification to the list
        setNotifications(prev => [data.data, ...prev]);
        setUnreadCount(prev => prev + 1);
      } else if (data.type === 'unread_count') {
        setUnreadCount(data.data.total);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
    };

    // Store reference for cleanup
    window.notificationEventSource = eventSource;

    return () => {
      eventSource.close();
    };
  };

  const markAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`/api/notifications/${notificationId}/read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      // Update local state
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      const token = localStorage.getItem('token');
      await fetch('/api/notifications/mark-all-read', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      // Update local state
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  const getFilteredNotifications = () => {
    let filtered = notifications;

    switch (activeTab) {
      case 'unread':
        filtered = notifications.filter(n => !n.is_read);
        break;
      case 'messages':
        filtered = notifications.filter(n =>
          n.event_type === 'MessageReceived' ||
          n.payload?.exchange_id
        );
        break;
      case 'system':
        filtered = notifications.filter(n =>
          n.event_type === 'SystemWarning' ||
          n.event_type === 'BanIssued'
        );
        break;
      default:
        // 'all' - show all
        break;
    }

    return filtered;
  };

  const getNotificationIcon = (eventType) => {
    switch (eventType) {
      case 'MessageReceived':
        return '💬';
      case 'OfferMatched':
        return '🤝';
      case 'ExchangeCreated':
        return '📋';
      case 'ExchangeCompleted':
        return '✅';
      case 'ReviewReceived':
        return '⭐';
      case 'SystemWarning':
        return '⚠️';
      case 'BanIssued':
        return '🚫';
      default:
        return '🔔';
    }
  };

  const getNotificationColor = (eventType) => {
    switch (eventType) {
      case 'MessageReceived':
        return 'message';
      case 'SystemWarning':
      case 'BanIssued':
        return 'warning';
      case 'ExchangeCompleted':
      case 'ReviewReceived':
        return 'success';
      default:
        return 'info';
    }
  };

  if (!isOpen) return null;

  const filteredNotifications = getFilteredNotifications();

  return (
    <div className="notification-drawer">
      <div className="notification-header">
        <h3>Уведомления</h3>
        {unreadCount > 0 && (
          <span className="unread-badge">{unreadCount}</span>
        )}
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      <div className="notification-tabs">
        <button
          className={`tab-button ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          Все ({notifications.length})
        </button>
        <button
          className={`tab-button ${activeTab === 'unread' ? 'active' : ''}`}
          onClick={() => setActiveTab('unread')}
        >
          Непрочитанные ({unreadCount})
        </button>
        <button
          className={`tab-button ${activeTab === 'messages' ? 'active' : ''}`}
          onClick={() => setActiveTab('messages')}
        >
          Сообщения
        </button>
        <button
          className={`tab-button ${activeTab === 'system' ? 'active' : ''}`}
          onClick={() => setActiveTab('system')}
        >
          Системные
        </button>
      </div>

      <div className="notification-actions">
        {unreadCount > 0 && (
          <button className="mark-all-read-button" onClick={markAllAsRead}>
            Отметить все как прочитанные
          </button>
        )}
      </div>

      <div className="notifications-list">
        {filteredNotifications.length === 0 ? (
          <div className="empty-state">
            {activeTab === 'unread' ? 'Нет непрочитанных уведомлений' : 'Нет уведомлений'}
          </div>
        ) : (
          filteredNotifications.map((notification) => (
            <div
              key={notification.id}
              className={`notification-item ${!notification.is_read ? 'unread' : ''} ${getNotificationColor(notification.event_type)}`}
              onClick={() => !notification.is_read && markAsRead(notification.id)}
            >
              <div className="notification-icon">
                {getNotificationIcon(notification.event_type)}
              </div>

              <div className="notification-content">
                <div className="notification-title">
                  {notification.event_type === 'MessageReceived' && 'Новое сообщение'}
                  {notification.event_type === 'OfferMatched' && 'Найден подходящий обмен'}
                  {notification.event_type === 'ExchangeCreated' && 'Создан новый обмен'}
                  {notification.event_type === 'ExchangeCompleted' && 'Обмен завершен'}
                  {notification.event_type === 'ReviewReceived' && 'Получен новый отзыв'}
                  {notification.event_type === 'SystemWarning' && 'Системное уведомление'}
                  {notification.event_type === 'BanIssued' && 'Аккаунт заблокирован'}
                </div>

                <div className="notification-text">
                  {/* Add specific text based on notification type */}
                  {notification.payload?.exchange_id && `Обмен #${notification.payload.exchange_id}`}
                  {notification.payload?.rating && `Рейтинг: ${notification.payload.rating}⭐`}
                </div>

                <div className="notification-time">
                  {notification.created_at ? new Date(notification.created_at).toLocaleString() : ''}
                </div>
              </div>

              {!notification.is_read && (
                <div className="unread-indicator"></div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NotificationDrawer;
