import React, { useEffect } from 'react';
import { Card, Form, InputNumber, Switch, Button, message, Input } from 'antd';
import { api } from '../../api/client';

export default function SystemSettings() {
  const [form] = Form.useForm();

  const fetchSettings = async () => {
    try {
      const res = await api.get('/admin/settings');
      if (res.data) form.setFieldsValue(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const onFinish = async (values) => {
    try {
      await api.patch('/admin/settings', values);
      message.success("Settings updated successfully");
    } catch (e) {
      message.error("Failed to update settings");
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px' }}>
      <h2>System Settings</h2>
      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ cgpa_floor: 6.0, student_self_reg: true, academic_year: '2026-27', primary_color: '#1890ff' }}>
          <Form.Item name="academic_year" label="Academic Year" rules={[{ required: true }]}>
            <Input placeholder="e.g. 2026-27" />
          </Form.Item>
          
          <Form.Item name="cgpa_floor" label="Global CGPA Floor (default for new drives)" rules={[{ required: true }]}>
            <InputNumber min={0} max={10} step={0.1} />
          </Form.Item>
          
          <Form.Item name="student_self_reg" label="Allow Student Self-Registration" valuePropName="checked">
            <Switch />
          </Form.Item>
          
          <Form.Item name="notification_templates" label="Default Notification Template Body">
             <Input.TextArea rows={4} placeholder="Hello {name},\n\n..." />
          </Form.Item>

          <Form.Item name="branding_logo" label="Branding Logo URL">
             <Input placeholder="https://example.com/logo.png" />
          </Form.Item>

          <Form.Item name="primary_color" label="Primary Color (Hex)">
             <Input type="color" style={{ width: 100, padding: 0 }} />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit">Save Settings</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
