import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { productsAPI, categoriesAPI, uploadsAPI } from '../../services/api';

const AdminProducts = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [uploadingThumbnail, setUploadingThumbnail] = useState(false);
  const [uploadingImages, setUploadingImages] = useState(false);
  const thumbnailInputRef = useRef(null);
  const imagesInputRef = useRef(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: 0,
    discount_percentage: 0,
    rating: 0,
    stock: 0,
    brand: '',
    thumbnail: '',
    images: [],
    is_published: true,
    category_id: ''
  });
  const [error, setError] = useState('');
  const limit = 10;

  useEffect(() => {
    fetchProducts();
    fetchCategories();
  }, [page]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await productsAPI.getAll(page, limit);
      setProducts(response.data.data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
    setLoading(false);
  };

  const fetchCategories = async () => {
    try {
      const response = await categoriesAPI.getAll(1, 100);
      setCategories(response.data.data || []);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    let newValue;
    
    if (type === 'checkbox') {
      newValue = checked;
    } else if (type === 'number') {
      // Handle empty input as empty string to allow user to clear and retype
      newValue = value === '' ? '' : parseFloat(value);
    } else {
      newValue = value;
    }
    
    setFormData({
      ...formData,
      [name]: newValue
    });
  };

  const handleImagesChange = (e) => {
    const imagesArray = e.target.value.split(',').map(img => img.trim()).filter(img => img);
    setFormData({ ...formData, images: imagesArray });
  };

  // Handle thumbnail upload
  const handleThumbnailUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadingThumbnail(true);
    setError('');
    try {
      const response = await uploadsAPI.uploadImage(file);
      const imageUrl = `/api${response.data.url}`;
      setFormData(prev => ({ ...prev, thumbnail: imageUrl }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload thumbnail');
    }
    setUploadingThumbnail(false);
  };

  // Handle multiple images upload
  const handleImagesUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploadingImages(true);
    setError('');
    try {
      const response = await uploadsAPI.uploadMultipleImages(files);
      const newUrls = response.data.uploaded.map(img => `/api${img.url}`);
      setFormData(prev => ({ ...prev, images: [...prev.images, ...newUrls] }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload images');
    }
    setUploadingImages(false);
  };

  // Remove an image from the images array
  const removeImage = (index) => {
    setFormData(prev => ({
      ...prev,
      images: prev.images.filter((_, i) => i !== index)
    }));
  };

  const openCreateModal = () => {
    setEditingProduct(null);
    setFormData({
      title: '',
      description: '',
      price: 0,
      discount_percentage: 0,
      rating: 0,
      stock: 0,
      brand: '',
      thumbnail: '',
      images: [],
      is_published: true,
      category_id: categories[0]?.id || ''
    });
    setError('');
    setShowModal(true);
  };

  const openEditModal = (product) => {
    setEditingProduct(product);
    setFormData({
      title: product.title,
      description: product.description || '',
      price: product.price,
      discount_percentage: product.discount_percentage,
      rating: product.rating,
      stock: product.stock,
      brand: product.brand,
      thumbnail: product.thumbnail,
      images: product.images || [],
      is_published: product.is_published,
      category_id: product.category_id
    });
    setError('');
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const productData = {
        ...formData,
        price: formData.price === '' ? 0 : parseFloat(formData.price),
        discount_percentage: formData.discount_percentage === '' ? 0 : parseFloat(formData.discount_percentage),
        stock: formData.stock === '' ? 0 : parseInt(formData.stock),
        rating: formData.rating === '' ? 0 : parseFloat(formData.rating),
        category_id: parseInt(formData.category_id),
        created_at: new Date().toISOString()
      };

      if (editingProduct) {
        await productsAPI.update(editingProduct.id, productData);
      } else {
        await productsAPI.create(productData);
      }
      
      setShowModal(false);
      fetchProducts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save product');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    
    try {
      await productsAPI.delete(id);
      fetchProducts();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete product');
    }
  };

  return (
    <div className="admin-page">
      <h1>Manage Products</h1>
      <Link to="/admin" style={{ marginBottom: '20px', display: 'inline-block' }}>← Back to Dashboard</Link>

      <div className="admin-table-container">
        <div className="admin-table-header">
          <h2>Products List</h2>
          <button onClick={openCreateModal} className="btn btn-success">+ Add Product</button>
        </div>

        {loading ? (
          <div className="loading">Loading products...</div>
        ) : (
          <>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Image</th>
                  <th>Title</th>
                  <th>Brand</th>
                  <th>Price</th>
                  <th>Stock</th>
                  <th>Published</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map(product => (
                  <tr key={product.id}>
                    <td>{product.id}</td>
                    <td>
                      <img 
                        src={product.thumbnail || 'https://via.placeholder.com/50'} 
                        alt={product.title}
                        style={{ width: '50px', height: '50px', objectFit: 'cover', borderRadius: '4px' }}
                        onError={(e) => { e.target.src = 'https://via.placeholder.com/50'; }}
                      />
                    </td>
                    <td>{product.title}</td>
                    <td>{product.brand}</td>
                    <td>${product.price}</td>
                    <td>{product.stock}</td>
                    <td>{product.is_published ? '✅' : '❌'}</td>
                    <td className="actions">
                      <button onClick={() => openEditModal(product)} className="btn btn-primary">Edit</button>
                      <button onClick={() => handleDelete(product.id)} className="btn btn-danger">Delete</button>
                    </td>
                  </tr>
                ))}
                {products.length === 0 && (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>
                      No products found. Add your first product!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            <div className="pagination">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                Previous
              </button>
              <button className="active">{page}</button>
              <button onClick={() => setPage(p => p + 1)} disabled={products.length < limit}>
                Next
              </button>
            </div>
          </>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingProduct ? 'Edit Product' : 'Add New Product'}</h2>
            
            {error && <div className="error-message">{error}</div>}
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Title *</label>
                <input type="text" name="title" value={formData.title} onChange={handleChange} required />
              </div>
              
              <div className="form-group">
                <label>Description</label>
                <textarea name="description" value={formData.description} onChange={handleChange} rows="3" />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Price *</label>
                  <input 
                    type="number" 
                    name="price" 
                    value={formData.price === '' ? '' : formData.price} 
                    onChange={handleChange} 
                    onFocus={(e) => e.target.value === '0' && e.target.select()}
                    required 
                    min="0" 
                    step="0.01"
                  />
                </div>
                
                <div className="form-group">
                  <label>Discount %</label>
                  <input 
                    type="number" 
                    name="discount_percentage" 
                    value={formData.discount_percentage === '' ? '' : formData.discount_percentage} 
                    onChange={handleChange} 
                    onFocus={(e) => e.target.value === '0' && e.target.select()}
                    min="0" 
                    max="100" 
                    step="0.1" 
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Stock *</label>
                  <input 
                    type="number" 
                    name="stock" 
                    value={formData.stock === '' ? '' : formData.stock} 
                    onChange={handleChange} 
                    onFocus={(e) => e.target.value === '0' && e.target.select()}
                    required 
                    min="0" 
                  />
                </div>
                
                <div className="form-group">
                  <label>Rating</label>
                  <input 
                    type="number" 
                    name="rating" 
                    value={formData.rating === '' ? '' : formData.rating} 
                    onChange={handleChange} 
                    onFocus={(e) => e.target.value === '0' && e.target.select()}
                    min="0" 
                    max="5" 
                    step="0.1" 
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Brand *</label>
                <input type="text" name="brand" value={formData.brand} onChange={handleChange} required />
              </div>
              
              <div className="form-group">
                <label>Category *</label>
                <select name="category_id" value={formData.category_id} onChange={handleChange} required>
                  <option value="">Select Category</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>Thumbnail *</label>
                <div className="upload-section">
                  <input 
                    type="file" 
                    accept="image/*" 
                    onChange={handleThumbnailUpload}
                    ref={thumbnailInputRef}
                    style={{ display: 'none' }}
                  />
                  <button 
                    type="button" 
                    onClick={() => thumbnailInputRef.current.click()}
                    className="btn btn-secondary"
                    disabled={uploadingThumbnail}
                  >
                    {uploadingThumbnail ? '⏳ Uploading...' : '📁 Upload Thumbnail'}
                  </button>
                  {formData.thumbnail && (
                    <div className="thumbnail-preview">
                      <img 
                        src={formData.thumbnail} 
                        alt="Thumbnail preview" 
                        style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '4px', marginLeft: '10px' }}
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                      <span className="thumbnail-url" style={{ marginLeft: '10px', fontSize: '12px', color: '#666' }}>
                        {formData.thumbnail.split('/').pop()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="form-group">
                <label>Additional Images</label>
                <div className="upload-section">
                  <input 
                    type="file" 
                    accept="image/*" 
                    multiple
                    onChange={handleImagesUpload}
                    ref={imagesInputRef}
                    style={{ display: 'none' }}
                  />
                  <button 
                    type="button" 
                    onClick={() => imagesInputRef.current.click()}
                    className="btn btn-secondary"
                    disabled={uploadingImages}
                  >
                    {uploadingImages ? '⏳ Uploading...' : '📁 Add Images'}
                  </button>
                </div>
                {formData.images.length > 0 && (
                  <div className="images-preview" style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '10px' }}>
                    {formData.images.map((img, index) => (
                      <div key={index} style={{ position: 'relative' }}>
                        <img 
                          src={img} 
                          alt={`Product ${index + 1}`}
                          style={{ width: '60px', height: '60px', objectFit: 'cover', borderRadius: '4px' }}
                          onError={(e) => { e.target.style.display = 'none'; }}
                        />
                        <button
                          type="button"
                          onClick={() => removeImage(index)}
                          style={{
                            position: 'absolute',
                            top: '-5px',
                            right: '-5px',
                            background: '#e74c3c',
                            color: 'white',
                            border: 'none',
                            borderRadius: '50%',
                            width: '20px',
                            height: '20px',
                            cursor: 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="form-group">
                <label>
                  <input type="checkbox" name="is_published" checked={formData.is_published} onChange={handleChange} />
                  {' '}Published
                </label>
              </div>
              
              <div className="modal-actions">
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-success">
                  {editingProduct ? 'Update Product' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminProducts;
