import React, { useState, useEffect } from 'react';
import { List, Typography, Badge, Button, Popconfirm, Tabs, Checkbox, Space, message, Select } from 'antd';
import { api } from '../../api/client';

const { Title, Text } = Typography;

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [selectedIds, setSelectedIds] = useState([]);
  
  const [activeTab, setActiveTab] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const fetchNotifs = async (pageNum = 1, append = false) => {
    setLoading(true);
    try {
      const params = { page: pageNum, page_size: 20 };
      if (activeTab === 'unread') params.is_read = false;
      if (categoryFilter !== 'ALL') params.type = categoryFilter;

      const res = await api.get(`/notifications`, { params });
      
      const newNotifs = res.data?.data || [];
      const totalPages = res.data?.meta?.total_pages || 1;
      
      if (append) {
        setNotifications(prev => [...prev, ...newNotifs]);
      } else {
        setNotifications(newNotifs);
      }
      setHasMore(pageNum < totalPages);
      setPage(pageNum);
    } catch(e) {
        message.error("Failed to fetch notifications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs(1, false);
    setSelectedIds([]);
  }, [activeTab, categoryFilter]);

  const handleDelete = async (id) => {
    try {
      await api.delete(`/notifications/${id}`);
      setNotifications(prev => prev.filter(n => n.id !== id));
      message.success("Deleted");
    } catch(e) {
      message.error("Failed to delete");
    }
  };

  const handleBulkMarkRead = async () => {
    try {
      await Promise.all(selectedIds.map(id => api.post(`/notifications/${id}/read`)));
      message.success("Marked selected as read");
      setSelectedIds([]);
      fetchNotifs(1, false);
    } catch(e) {
      message.error("Failed to update");
    }
  };

  const handleBulkDelete = async () => {
    try {
      await Promise.all(selectedIds.map(id => api.delete(`/notifications/${id}`)));
      message.success("Deleted selected");
      setSelectedIds([]);
      fetchNotifs(1, false);
    } catch(e) {
      message.error("Failed to delete");
    }
  };

  const toggleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(notifications.map(n => n.id));
    } else {
      setSelectedIds([]);
    }
  };

  const tabItems = [
    { key: 'all', label: 'All' },
    { key: 'unread', label: 'Unread' },
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto', background: '#fff', minHeight: '100vh' }}>
      <Title level={2}>Inbox</Title>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', alignItems: 'center' }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} style={{ marginBottom: 0 }} />
        <Select 
           value={categoryFilter}
           onChange={setCategoryFilter}
           style={{ width: 200 }}
           options={[
             { value: 'ALL', label: 'All Categories' },
             { value: 'DRIVE_OPEN', label: 'Drive Alerts' },
             { value: 'APPLICATION_STATUS', label: 'Application Updates' },
             { value: 'ASSESSMENT_RESULT', label: 'Assessments' }
           ]}
        />
      </div>

      <div style={{ marginBottom: '16px', padding: '8px 16px', background: '#f5f5f5', borderRadius: '4px', display: 'flex', justifyContent: 'space-between' }}>
        <Checkbox 
           checked={selectedIds.length > 0 && selectedIds.length === notifications.length} 
           indeterminate={selectedIds.length > 0 && selectedIds.length < notifications.length}
           onChange={toggleSelectAll}
        >
          Select All
        </Checkbox>
        {selectedIds.length > 0 && (
          <Space>
            <Button size="small" onClick={handleBulkMarkRead}>Mark Read</Button>
            <Button size="small" danger onClick={handleBulkDelete}>Delete</Button>
          </Space>
        )}
      </div>
      
      <List
        loading={loading}
        itemLayout="horizontal"
        dataSource={notifications}
        locale={{ emptyText: 'No notifications found' }}
        renderItem={item => (
          <List.Item
            style={{ background: item.is_read ? 'transparent' : '#f0f8ff', padding: '12px', borderBottom: '1px solid #f0f0f0' }}
            actions={[
              <Popconfirm title="Delete this notification?" onConfirm={() => handleDelete(item.id)}>
                <Button type="link" danger>Delete</Button>
              </Popconfirm>
            ]}
          >
            <div style={{ marginRight: '16px', paddingTop: '4px' }}>
              <Checkbox 
                 checked={selectedIds.includes(item.id)}
                 onChange={(e) => {
                   if (e.target.checked) setSelectedIds(prev => [...prev, item.id]);
                   else setSelectedIds(prev => prev.filter(id => id !== item.id));
                 }}
              />
            </div>
            <List.Item.Meta
              avatar={<Badge dot={!item.is_read} color={item.priority === 'critical' ? 'red' : 'blue'} />}
              title={<a href={item.link || '#'} style={{ fontWeight: item.is_read ? 'normal' : 'bold' }}>{item.title}</a>}
              description={
                <div>
                  <Text>{item.message}</Text>
                  <div style={{ marginTop: '4px', color: '#888', fontSize: '12px' }}>
                    {new Date(item.created_at).toLocaleString()} | {item.type}
                  </div>
                </div>
              }
            />
          </List.Item>
        )}
      />
      
      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <Button onClick={() => fetchNotifs(page + 1, true)} loading={loading}>Load More</Button>
        </div>
      )}
    </div>
  );
}
