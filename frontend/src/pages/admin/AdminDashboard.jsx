import React, { useState, useEffect } from 'react';
import { Card, Result, Spin, Row, Col, Typography, Statistic, List, Tag, Progress } from 'antd';
import { UserOutlined, FileDoneOutlined, AimOutlined, WarningOutlined } from '@ant-design/icons';
import { api } from '../../api/client';

const { Title } = Typography;

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [health, setHealth] = useState(null);
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [metRes, hltRes, audRes] = await Promise.all([
        api.get('/admin/metrics/summary'),
        api.get('/health'),
        api.get('/system/audit-logs?page_size=10')
      ]);
      setMetrics(metRes.data);
      setHealth(hltRes.data);
      setAudits(audRes.data?.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Health and Metrics polling every 30s
    const intv30 = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(intv30);
  }, []);

  useEffect(() => {
    // Audit log polling every 10s
    const fetchAudits = async () => {
      try {
        const audRes = await api.get('/system/audit-logs?page_size=10');
        setAudits(audRes.data?.data || []);
      } catch (e) {}
    };
    const intv10 = setInterval(fetchAudits, 10000);
    return () => clearInterval(intv10);
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '3rem auto' }} />;
  if (!metrics) return <Result status="error" title="Failed to load metrics" />;

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Admin Super Panel</Title>
      
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic title="Total Users" value={metrics.total_users} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Active Students" value={metrics.active_students} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Open Drives" value={metrics.drives_open} prefix={<AimOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="System Errors (24h)" value={metrics.error_rate_24h_percent} suffix="%" prefix={<WarningOutlined />} valueStyle={{ color: '#cf1322' }} />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#888' }}>
               Sparkline Trend: {'>'}{'>'}{'>'}{metrics.error_rate_24h_percent > 5 ? 'Elevated' : 'Stable'}
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card title="System Health Gauges">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', alignItems: 'center' }}>
               <div>
                  <h4>Database</h4>
                  <Progress type="dashboard" percent={health?.db?.connected ? 100 : 0} format={() => `${health?.db?.latency_ms || 0}ms`} status={health?.db?.connected ? 'success' : 'exception'} />
               </div>
               <div>
                  <h4>Redis Engine</h4>
                  <Progress type="dashboard" percent={health?.redis?.connected ? 100 : 0} format={() => `${health?.redis?.latency_ms || 0}ms`} status={health?.redis?.connected ? 'success' : 'exception'} />
               </div>
               <div>
                 <small>Uptime: {health?.uptime_seconds}s</small>
               </div>
            </div>
          </Card>
        </Col>
        <Col span={16}>
          <Card title="Recent Activity Logs (Live)">
             <List
               size="small"
               dataSource={audits}
               renderItem={item => (
                 <List.Item>
                   <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between' }}>
                     <div>
                       <Tag color={item.event_type.includes('ERROR') || item.event_type.includes('UNAUTH') ? 'red' : 'blue'}>{item.event_type}</Tag>
                       <Typography.Text strong>{item.resource_type}</Typography.Text> - {JSON.stringify(item.details)}
                     </div>
                     <div style={{ color: '#888', fontSize: '12px' }}>
                       {new Date(item.created_at).toLocaleTimeString()}
                     </div>
                   </div>
                 </List.Item>
               )}
             />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
