import React, { useState, useEffect } from 'react';
import orderApi from '../../../api/orderApi';

const ReturnRequestsModal = ({ onClose }) => {
  const [requests, setRequests] = useState([]);
  const [selectedReq, setSelectedReq] = useState(null); // Yêu cầu đang xem chi tiết
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);

  // Load danh sách yêu cầu
  const fetchRequests = async () => {
    try {
      setLoading(true);
      const res = await orderApi.getAllReturns({ _t: Date.now() }); // Chống cache
      setRequests(Array.isArray(res) ? res : (res.data || []));
    } catch (error) { console.error(error); } finally { setLoading(false); }
  };

  useEffect(() => { fetchRequests(); }, []);

  // Xử lý Duyệt/Từ chối
  const handleAction = async (action) => {
    if (!selectedReq) return;
    
    // Nếu từ chối thì hỏi lý do
    let reason = '';
    if (action === 'REJECT') {
        reason = prompt("Nhập lý do từ chối yêu cầu này:");
        if (!reason) return; // Hủy nếu không nhập
    } else {
        if (!window.confirm("Bạn chắc chắn muốn DUYỆT yêu cầu trả hàng này?")) return;
    }

    setProcessing(true);
    try {
        if (action === 'APPROVE') {
            await orderApi.approveReturn(selectedReq.return_id);
            alert(" Đã duyệt yêu cầu! Hệ thống sẽ chuyển sang trạng thái chờ hoàn tiền.");
        } else {
            await orderApi.rejectReturn(selectedReq.return_id, reason);
            alert(" Đã từ chối yêu cầu.");
        }
        // Refresh lại danh sách và đóng chi tiết
        fetchRequests();
        setSelectedReq(null);
    } catch (error) {
        alert("Lỗi xử lý: " + (error.response?.data?.detail || error.message));
    } finally {
        setProcessing(false);
    }
  };

  const getStatusColor = (status) => {
      if(status === 'PENDING') return '#f59e0b'; // Cam
      if(status === 'APPROVED') return '#10b981'; // Xanh lá
      if(status === 'REJECTED') return '#ef4444'; // Đỏ
      return '#6b7280';
  };

  const formatMoney = (val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);

  return (
    <div className="modal-overlay" style={{zIndex: 2000}}>
      <div className="modal-content" style={{width:'900px', maxWidth:'95%', height:'85vh', display:'flex', flexDirection:'column', padding:0}}>
        
        {/* Header */}
        <div className="modal-header" style={{padding:'15px 20px', borderBottom:'1px solid #eee'}}>
            <h3 style={{margin:0}}>🛡️ Quản lý Yêu cầu Trả hàng / Hoàn tiền</h3>
            <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        {/* Body: Chia 2 cột */}
        <div className="modal-body" style={{flex:1, display:'flex', overflow:'hidden'}}>
            
            {/* Cột Trái: Danh sách (30%) */}
            <div style={{width:'35%', borderRight:'1px solid #eee', overflowY:'auto', background:'#f9fafb'}}>
                {loading ? <p style={{padding:20}}>Đang tải...</p> : requests.map(req => (
                    <div 
                        key={req.return_id} 
                        onClick={() => setSelectedReq(req)}
                        style={{
                            padding:'15px', borderBottom:'1px solid #eee', cursor:'pointer',
                            background: selectedReq?.return_id === req.return_id ? '#e0f2fe' : 'transparent'
                        }}
                    >
                        <div style={{display:'flex', justifyContent:'space-between', marginBottom:'5px'}}>
                            <strong style={{color:'#4361ee'}}>#{req.return_id}</strong>
                            <span style={{fontSize:'11px', fontWeight:'bold', color: getStatusColor(req.status)}}>{req.status}</span>
                        </div>
                        <div style={{fontSize:'13px', color:'#333'}}>Đơn hàng: <strong>#{req.order_id}</strong></div>
                        <div style={{fontSize:'12px', color:'#666', marginTop:'3px'}}>{new Date(req.created_at).toLocaleString('vi-VN')}</div>
                    </div>
                ))}
                {requests.length === 0 && !loading && <p style={{padding:20, color:'#888'}}>Không có yêu cầu nào.</p>}
            </div>

            {/* Cột Phải: Chi tiết (70%) */}
            <div style={{flex:1, padding:'20px', overflowY:'auto', background:'white'}}>
                {selectedReq ? (
                    <div>
                        <div style={{marginBottom:'20px', borderBottom:'1px solid #eee', paddingBottom:'15px'}}>
                            <h4 style={{margin:'0 0 10px 0', color:'#111827'}}>Chi tiết yêu cầu #{selectedReq.return_id}</h4>
                            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'10px', fontSize:'14px'}}>
                                <div>Lý do: <strong>{selectedReq.return_reason}</strong></div>
                                <div>Trạng thái: <strong style={{color: getStatusColor(selectedReq.status)}}>{selectedReq.status}</strong></div>
                                <div style={{gridColumn:'span 2'}}>Ghi chú khách: <span style={{fontStyle:'italic', color:'#555'}}>{selectedReq.reason_detail || "Không có"}</span></div>
                            </div>
                        </div>

                        {/* Ảnh bằng chứng (Nếu có) */}
                        {selectedReq.images && selectedReq.images.length > 0 && (
                            <div style={{marginBottom:'20px'}}>
                                <h5 style={{margin:'0 0 10px 0'}}>📸 Ảnh bằng chứng:</h5>
                                <div style={{display:'flex', gap:'10px', overflowX:'auto'}}>
                                    {/* Parse JSON nếu images là string, hoặc dùng trực tiếp nếu là array */}
                                    {(typeof selectedReq.images === 'string' ? JSON.parse(selectedReq.images) : selectedReq.images).map((img, idx) => (
                                        <a key={idx} href={img} target="_blank" rel="noreferrer">
                                            <img src={img} alt="proof" style={{height:'80px', borderRadius:'4px', border:'1px solid #ddd'}} />
                                        </a>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Danh sách sản phẩm trả */}
                        <div style={{marginBottom:'20px'}}>
                            <h5 style={{margin:'0 0 10px 0'}}> Sản phẩm trả về:</h5>
                            <table style={{width:'100%', borderCollapse:'collapse', fontSize:'13px'}}>
                                <thead style={{background:'#f3f4f6'}}>
                                    <tr>
                                        <th style={{padding:'8px', border:'1px solid #ddd'}}>Sản phẩm</th>
                                        <th style={{padding:'8px', border:'1px solid #ddd'}}>SL</th>
                                        <th style={{padding:'8px', border:'1px solid #ddd'}}>Tình trạng</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {/* Giả sử API trả về return_items trong object chi tiết */}
                                    {(selectedReq.return_items || []).map((item, idx) => (
                                        <tr key={idx}>
                                            <td style={{padding:'8px', border:'1px solid #ddd'}}>Product ID: {item.product_id}</td>
                                            <td style={{padding:'8px', border:'1px solid #ddd', textAlign:'center'}}>{item.quantity}</td>
                                            <td style={{padding:'8px', border:'1px solid #ddd'}}>{item.condition}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Action Buttons (Chỉ hiện khi PENDING) */}
                        {selectedReq.status === 'PENDING' && (
                            <div style={{marginTop:'30px', display:'flex', gap:'10px', justifyContent:'flex-end'}}>
                                <button 
                                    onClick={() => handleAction('REJECT')} disabled={processing}
                                    style={{padding:'10px 20px', background:'#fee2e2', color:'#b91c1c', border:'1px solid #fca5a5', borderRadius:'6px', cursor:'pointer', fontWeight:'bold'}}
                                >
                                     Từ chối
                                </button>
                                <button 
                                    onClick={() => handleAction('APPROVE')} disabled={processing}
                                    style={{padding:'10px 20px', background:'#10b981', color:'white', border:'none', borderRadius:'6px', cursor:'pointer', fontWeight:'bold'}}
                                >
                                     Chấp thuận & Hoàn tiền
                                </button>
                            </div>
                        )}
                    </div>
                ) : (
                    <div style={{display:'flex', alignItems:'center', justifyContent:'center', height:'100%', color:'#9ca3af', flexDirection:'column'}}>
                        <div style={{fontSize:'40px'}}></div>
                        <p>Chọn một yêu cầu bên trái để xem chi tiết</p>
                    </div>
                )}
            </div>
        </div>
      </div>
    </div>
  );
};

export default ReturnRequestsModal;