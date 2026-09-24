import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Upload, message, Switch, Select, Space, Input } from 'antd';
import { UploadOutlined, ExclamationCircleOutlined, SearchOutlined } from '@ant-design/icons';
import { api, BASE_URL } from '../../api/client';

const { confirm } = Modal;
const { Search } = Input;

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [roleFilter, setRoleFilter] = useState('');
  const [searchText, setSearchText] = useState('');

  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewData, setPreviewData] = useState([]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const fetchUsers = async (p = 1) => {
    setLoading(true);
    try {
      const params = { page: p, per_page: 50 };
      if (roleFilter) params.role = roleFilter;
      if (searchText) params.search = searchText;

      const res = await api.get('/admin/users', { params });
      setUsers(res.data?.data || []);
      setTotal(res.data?.meta?.total || 0);
      setPage(p);
    } catch(e) {
       message.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers(1);
  }, [roleFilter]);

  const handleRoleChange = async (userId, value) => {
    try {
      await api.patch(`/admin/users/${userId}/role?new_role=${value}`);
      fetchUsers(page);
      message.success('Role updated');
    } catch(e) { message.error("Failed"); }
  };

  const handleStatusChange = async (userId, isActive) => {
    try {
      await api.patch(`/admin/users/${userId}/status?is_active=${isActive}`);
      fetchUsers(page);
      message.success('Status updated');
    } catch(e) { message.error("Failed"); }
  };

  const handleResetPassword = (userId) => {
    confirm({
      title: 'Generate Password Reset Link?',
      icon: <ExclamationCircleOutlined />,
      content: 'This will generate a one-time secure link to reset this user\'s password.',
      onOk: async () => {
        try {
          const res = await api.post(`/admin/users/${userId}/generate-reset-link`);
          Modal.info({
            title: 'Password Reset Link',
            width: 600,
            content: (
              <div>
                <p>Share this link with the user securely:</p>
                <a href={res.data.reset_link}>{window.location.origin}{res.data.reset_link}</a>
              </div>
            )
          });
        } catch(e) { message.error("Failed to generate link"); }
      }
    });
  };

  const parseCSVPreview = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const rows = text.split('\\n').filter(r => r.trim() !== '');
      if (rows.length < 2) return message.error("CSV empty or missing headers");
      
      const headers = rows[0].split(',').map(h => h.trim().replace(/["']/g, ''));
      const parsedRows = rows.slice(1, 21).map((r, i) => {
         const cols = r.split(',').map(c => c.trim().replace(/["']/g, ''));
         let obj = { key: i };
         headers.forEach((h, j) => { obj[h] = cols[j]; });
         return obj;
      });
      
      setPreviewData(parsedRows);
      setUploadFile(file);
      setPreviewModalVisible(true);
    };
    reader.readAsText(file);
  };

  const executeBulkImport = async () => {
    if (!uploadFile) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const res = await api.post('/admin/users/bulk-import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const results = res.data.results || [];
      const successes = results.filter(r => r.status === 'success');
      
      let csvContent = "data:text/csv;charset=utf-8,Email,Status,Reset_Link\\n";
      results.forEach(r => {
         csvContent += `${r.email},${r.status},${window.location.origin}${r.reset_link || ''}\\n`;
      });
      const encodedUri = encodeURI(csvContent);
      
      setPreviewModalVisible(false);
      setUploadFile(null);
      
      Modal.success({
         title: 'Bulk Import Complete',
         content: (
           <div>
             <p>{successes.length} created, {results.length - successes.length} failed.</p>
             <a href={encodedUri} download="import_results.csv">Download Reset Links (CSV)</a>
             <p style={{color:'red', marginTop: '10px'}}><small>Save the CSV immediately. Links cannot be retrieved later.</small></p>
           </div>
         ),
         onOk: () => fetchUsers(page)
      });
    } catch(e) {
      message.error("Import failed");
    } finally {
      setUploading(false);
    }
  };

  const columns = [
    { title: 'Name', render: (_, record) => `${record.first_name} ${record.last_name}` },
    { title: 'Email', dataIndex: 'email' },
    { title: 'Role', dataIndex: 'role', render: (val, record) => (
       <Select value={val} onChange={(newVal) => handleRoleChange(record.id, newVal)} style={{width: 100}}>
         <Select.Option value="student">Student</Select.Option>
         <Select.Option value="tpo">TPO</Select.Option>
         <Select.Option value="admin">Admin</Select.Option>
       </Select>
    )},
    { title: 'Active', dataIndex: 'is_active', render: (val, record) => (
       <Switch checked={val} onChange={(checked) => handleStatusChange(record.id, checked)} />
    )},
    { title: 'Actions', render: (_, record) => (
       <Button type="link" onClick={() => handleResetPassword(record.id)}>Generate Reset Link</Button>
    )}
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2>User Management ({total})</h2>
        <Space>
           <Search 
              placeholder="Search users..." 
              onSearch={(val) => { setSearchText(val); fetchUsers(1); }} 
              style={{ width: 200 }} 
           />
           <Select defaultValue="" style={{ width: 120 }} onChange={(val) => setRoleFilter(val)}>
              <Select.Option value="">All Roles</Select.Option>
              <Select.Option value="student">Students</Select.Option>
              <Select.Option value="tpo">TPO</Select.Option>
              <Select.Option value="admin">Admin</Select.Option>
           </Select>
           <Upload 
              beforeUpload={(file) => { parseCSVPreview(file); return false; }} 
              showUploadList={false}
           >
             <Button icon={<UploadOutlined />} type="primary">Bulk Import CSV</Button>
           </Upload>
        </Space>
      </div>
      <Table 
        columns={columns} 
        dataSource={users} 
        rowKey="id" 
        loading={loading}
        pagination={{ 
          pageSize: 50, 
          total: total, 
          current: page,
          onChange: (p) => fetchUsers(p) 
        }} 
      />

      <Modal
        title="CSV Import Preview (First 20 Rows)"
        open={previewModalVisible}
        onCancel={() => { setPreviewModalVisible(false); setUploadFile(null); }}
        onOk={executeBulkImport}
        confirmLoading={uploading}
        width={800}
      >
         <Table 
            dataSource={previewData} 
            columns={previewData.length > 0 ? Object.keys(previewData[0]).filter(k => k !== 'key').map(k => ({ title: k, dataIndex: k })) : []} 
            pagination={false} 
            size="small" 
            scroll={{ x: 'max-content', y: 400 }}
         />
      </Modal>
    </div>
  );
}
