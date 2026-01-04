import React, { useState, useEffect } from 'react';
import productApi from '../../../api/productApi';

const CategoryManager = ({ onClose }) => {
  const [categories, setCategories] = useState([]);
  const [newName, setNewName] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchCats = async () => {
    try {
      const res = await productApi.getCategories();
      setCategories(Array.isArray(res) ? res : (res.data || []));
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchCats(); }, []);

  const handleAdd = async () => {
    if (!newName.trim()) return;
    setLoading(true);
    try {
        // Payload tạo category cơ bản
        await productApi.createCategory({ 
            category_name: newName, 
            is_active: true,
            slug: newName.toLowerCase().replace(/ /g, '-').replace(/[^\w-]+/g, '')
        });
        setNewName('');
        fetchCats();
    } catch (e) { 
        alert("Lỗi: " + (e.response?.data?.detail || e.message)); 
    } finally { setLoading(false); }
  };

  const handleDelete = async (id) => {
      if(window.confirm('Xóa danh mục này?')) {
          try { await productApi.deleteCategory(id); fetchCats(); } 
          catch(e) { alert('Không thể xóa (có thể đang chứa sản phẩm)'); }
      }
  }

  return (
    <div className="modal-overlay" onClick={onClose} style={{zIndex: 10001}}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{width:'500px'}}>
        <div className="modal-header">
            <h3> Quản lý Danh mục</h3>
            <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body" style={{padding:'20px'}}>
            <div style={{display:'flex', gap:'10px', marginBottom:'20px'}}>
                <input className="form-control" value={newName} onChange={e => setNewName(e.target.value)} placeholder="Nhập tên danh mục..." />
                <button className="btn-primary" onClick={handleAdd} disabled={loading} style={{width:'100px'}}>
                    {loading ? '...' : 'Thêm'}
                </button>
            </div>
            <div style={{maxHeight:'300px', overflowY:'auto', border:'1px solid #eee', borderRadius:'6px'}}>
                <table className="data-table" style={{marginTop:0}}>
                    <tbody>
                        {categories.map(c => (
                            <tr key={c.category_id}>
                                <td>{c.category_name}</td>
                                <td style={{textAlign:'right'}}>
                                    <button className="btn-icon delete" onClick={() => handleDelete(c.category_id)}>🗑️</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
      </div>
    </div>
  );
};
export default CategoryManager;