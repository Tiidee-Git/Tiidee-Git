import { useState, useEffect } from 'react';

export function useOffline() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [offlineQueue, setOfflineQueue] = useState([]);

  useEffect(() => {
    function handleOnline() {
      setIsOnline(true);
      // Process offline queue when back online
      processOfflineQueue();
    }

    function handleOffline() {
      setIsOnline(false);
    }

    function handleConnectionChange(event) {
      setIsOnline(event.detail.online);
      if (event.detail.online) {
        processOfflineQueue();
      }
    }

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('connectionchange', handleConnectionChange);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('connectionchange', handleConnectionChange);
    };
  }, []);

  const addToOfflineQueue = (action) => {
    const queueItem = {
      id: Date.now(),
      action,
      timestamp: new Date().toISOString()
    };
    
    setOfflineQueue(prev => [...prev, queueItem]);
    
    // Store in localStorage for persistence
    const existingQueue = JSON.parse(localStorage.getItem('offlineQueue') || '[]');
    existingQueue.push(queueItem);
    localStorage.setItem('offlineQueue', JSON.stringify(existingQueue));
  };

  const processOfflineQueue = async () => {
    const queue = JSON.parse(localStorage.getItem('offlineQueue') || '[]');
    
    for (const item of queue) {
      try {
        await item.action();
        // Remove processed item from queue
        const updatedQueue = queue.filter(q => q.id !== item.id);
        localStorage.setItem('offlineQueue', JSON.stringify(updatedQueue));
        setOfflineQueue(updatedQueue);
      } catch (error) {
        console.error('Failed to process offline queue item:', error);
      }
    }
  };

  const saveOfflineData = (key, data) => {
    try {
      localStorage.setItem(`offline_${key}`, JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('Failed to save offline data:', error);
      return false;
    }
  };

  const getOfflineData = (key) => {
    try {
      const data = localStorage.getItem(`offline_${key}`);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Failed to get offline data:', error);
      return null;
    }
  };

  const clearOfflineData = (key) => {
    try {
      localStorage.removeItem(`offline_${key}`);
      return true;
    } catch (error) {
      console.error('Failed to clear offline data:', error);
      return false;
    }
  };

  return {
    isOnline,
    offlineQueue,
    addToOfflineQueue,
    saveOfflineData,
    getOfflineData,
    clearOfflineData
  };
}

