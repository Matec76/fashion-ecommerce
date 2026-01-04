import React, { useState, useEffect } from 'react';
import productApi from '../../../api/productApi';

const CollectionManager = ({ onClose }) => {
  const [collections, setCollections] = useState([]);
  const [newName, setNewName] = useState('');
  const [loading, setLoading] = useState(false);
  const fetchCols = async () => {
    try {
      const res = await productApi.getCollections(); 
      setCollections(Array.isArray(res) ? res : (res.data || []));
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchCols(); }, []);

  const handleAdd = async () => {
    if (!newName.trim()) return;
    setLoading(true);
    try {
        const payload = { 
            collection_name: newName, 
            description: "New collection",
            is_active: true
        };
        const res = await productApi.createCollection(payload);
        const newItem = res.data || res; 
        if (newItem && (newItem.collection_id || newItem.id)) {
            setCollections(prev => [newItem, ...prev]); 
        } else {
            setTimeout(() => fetchCols(), 500);
        }

        setNewName('');
    } catch (e) { 
        alert(" Lỗi: " + (e.response?.data?.detail || e.message)); 
    } finally { 
        setLoading(false); 
    }
  };

  const handleDelete = async (id) => {
      if(window.confirm('Xóa bộ sưu tập này?')) {
          try { 
              await productApi.deleteCollection(id); 
              setCollections(prev => prev.filter(c => c.collection_id !== id));
          } 
          catch(e) { alert(' Lỗi xóa: ' + e.message); }
      }
  }

  return (
    <div className="modal-overlay" onClick={onClose} style={{zIndex: 10001}}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{width:'500px'}}>
        <div className="modal-header">
            <h3>🎗️ Quản lý Bộ sưu tập</h3>
            <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body" style={{padding:'20px'}}>
            <div style={{display:'flex', gap:'10px', marginBottom:'20px'}}>
                <input 
                    className="form-control" 
                    value={newName} 
                    onChange={e => setNewName(e.target.value)} 
                    onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
                    placeholder="Nhập tên bộ sưu tập..." 
                />
                <button className="btn-primary" onClick={handleAdd} disabled={loading} style={{width:'100px'}}>
                    {loading ? '...' : 'Thêm'}
                </button>
            </div>
            
            {/* Danh sách */}
            <div style={{maxHeight:'300px', overflowY:'auto', border:'1px solid #eee', borderRadius:'6px'}}>
                <table className="data-table" style={{marginTop:0}}>
                    <tbody>
                        {collections.length > 0 ? collections.map(c => (
                            <tr key={c.collection_id}>
                                <td style={{fontWeight: '500'}}>{c.collection_name}</td>
                                <td style={{textAlign:'right'}}>
                                    <button className="btn-icon delete" onClick={() => handleDelete(c.collection_id)} title="Xóa">🗑️</button>
                                </td>
                            </tr>
                        )) : (
                            <tr><td className="text-center" style={{color:'#999'}}>Chưa có bộ sưu tập nào</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
      </div>
    </div>
  );
};

export default CollectionManager;