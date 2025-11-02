'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ordersAPI, Order, OrderHistory, getUploadUrl } from '@/lib/api';

const statusLabels = {
  draft: 'Черновик',
  pending_confirmation: 'Ожидает подтверждения',
  confirmed: 'Подтвержден',
  in_progress: 'В работе',
  ready: 'Готов к доставке',
  delivered: 'Доставлен',
};

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  pending_confirmation: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-orange-100 text-orange-800',
  ready: 'bg-green-100 text-green-800',
  delivered: 'bg-purple-100 text-purple-800',
};

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [orderHistory, setOrderHistory] = useState<OrderHistory[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form states
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_phone: '',
    customer_address: '',
    phone_agreement_notes: '',
    customer_requirements: '',
    deadline: '',
    price: '',
    material_photo: null as File | null,
    furniture_photo: null as File | null,
  });

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const response = await ordersAPI.getOrders();
      setOrders(response.data);
    } catch (error: any) {
      console.error('Error loading orders:', error);
      // Check if it's a 401 or 403 error and redirect to login if needed
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.error('Authentication error, redirecting to login');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.customer_name.trim()) {
      alert('Пожалуйста, укажите имя заказчика');
      return;
    }
    if (!formData.customer_phone.trim()) {
      alert('Пожалуйста, укажите телефон');
      return;
    }
    if (!formData.customer_address.trim()) {
      alert('Пожалуйста, укажите адрес');
      return;
    }

    const data = new FormData();
    data.append('customer_name', formData.customer_name.trim());
    data.append('customer_phone', formData.customer_phone.trim());
    data.append('customer_address', formData.customer_address.trim());
    if (formData.phone_agreement_notes) {
      data.append('phone_agreement_notes', formData.phone_agreement_notes.trim());
    }

    try {
      await ordersAPI.createOrder(data);
      setShowCreateDialog(false);
      resetForm();
      loadOrders();
    } catch (error: any) {
      console.error('Error creating order:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при создании заказа';
      alert(errorMessage);
    }
  };

  const handleUpdateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;

    // Validate form
    if (!formData.customer_name.trim()) {
      alert('Пожалуйста, укажите имя заказчика');
      return;
    }
    if (!formData.customer_phone.trim()) {
      alert('Пожалуйста, укажите телефон');
      return;
    }
    if (!formData.customer_address.trim()) {
      alert('Пожалуйста, укажите адрес');
      return;
    }

    const data = new FormData();
    data.append('customer_name', formData.customer_name.trim());
    data.append('customer_phone', formData.customer_phone.trim());
    data.append('customer_address', formData.customer_address.trim());
    if (formData.phone_agreement_notes) {
      data.append('phone_agreement_notes', formData.phone_agreement_notes.trim());
    }

    try {
      await ordersAPI.updateOrder(selectedOrder.id, data);
      setShowEditDialog(false);
      resetForm();
      loadOrders();
    } catch (error: any) {
      console.error('Error updating order:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при обновлении заказа';
      alert(errorMessage);
    }
  };

  const handleAddDetails = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;

    // Validate form
    if (!formData.customer_requirements.trim()) {
      alert('Пожалуйста, укажите требования клиента');
      return;
    }
    if (!formData.deadline) {
      alert('Пожалуйста, укажите срок выполнения');
      return;
    }
    const price = parseInt(formData.price);
    if (isNaN(price) || price <= 0) {
      alert('Пожалуйста, укажите корректную цену (положительное число)');
      return;
    }

    const data = new FormData();
    data.append('customer_requirements', formData.customer_requirements.trim());
    data.append('deadline', formData.deadline);
    data.append('price', price.toString());
    if (formData.material_photo) {
      data.append('material_photo', formData.material_photo);
    }
    if (formData.furniture_photo) {
      data.append('furniture_photo', formData.furniture_photo);
    }

    try {
      await ordersAPI.addOrderDetails(selectedOrder.id, data);
      setShowDetailsDialog(false);
      resetForm();
      loadOrders();
    } catch (error: any) {
      console.error('Error adding details:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при добавлении деталей заказа';
      alert(errorMessage);
    }
  };

  const handleAction = async (orderId: number, action: string) => {
    try {
      switch (action) {
        case 'submit':
          await ordersAPI.submitOrder(orderId);
          break;
        case 'confirm':
          await ordersAPI.confirmOrder(orderId);
          break;
        case 'complete':
          await ordersAPI.completeOrder(orderId);
          break;
        case 'deliver':
          await ordersAPI.markDelivered(orderId);
          break;
      }
      loadOrders();
    } catch (error: any) {
      console.error(`Error ${action} order:`, error);
      const errorMessage = error.response?.data?.detail || `Ошибка при выполнении действия: ${action}`;
      alert(errorMessage);
    }
  };

  const handleViewOrder = async (order: Order) => {
    setSelectedOrder(order);
    try {
      const response = await ordersAPI.getOrderHistory(order.id);
      setOrderHistory(response.data);
    } catch (error) {
      console.error('Error loading order history:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      customer_name: '',
      customer_phone: '',
      customer_address: '',
      phone_agreement_notes: '',
      customer_requirements: '',
      deadline: '',
      price: '',
      material_photo: null,
      furniture_photo: null,
    });
  };

  const openEditDialog = (order: Order) => {
    setSelectedOrder(order);
    setFormData({
      customer_name: order.customer_name,
      customer_phone: order.customer_phone || '',
      customer_address: order.customer_address || '',
      phone_agreement_notes: order.phone_agreement_notes || '',
      customer_requirements: order.customer_requirements || '',
      deadline: order.deadline || '',
      price: order.price?.toString() || '',
      material_photo: null,
      furniture_photo: null,
    });
    setShowEditDialog(true);
  };

  const openDetailsDialog = (order: Order) => {
    setSelectedOrder(order);
    setFormData({
      customer_name: order.customer_name,
      customer_phone: order.customer_phone || '',
      customer_address: order.customer_address || '',
      phone_agreement_notes: order.phone_agreement_notes || '',
      customer_requirements: order.customer_requirements || '',
      deadline: order.deadline || '',
      price: order.price?.toString() || '',
      material_photo: null,
      furniture_photo: null,
    });
    setShowDetailsDialog(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Загрузка...</p>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold">CRM Перетяжка Мебели</h1>
              <p className="text-gray-600">Добро пожаловать, {user?.username} ({user?.role})</p>
            </div>
            <Button onClick={logout} variant="outline">
              Выйти
            </Button>
          </div>

          <div className="grid grid-cols-3 gap-2 mb-4">
            <Card className="p-2">
              <div className="text-center">
                <div className="text-xl font-bold text-blue-600">{orders.length}</div>
                <div className="text-xs text-gray-600">Всего</div>
              </div>
            </Card>
            <Card className="p-2">
              <div className="text-center">
                <div className="text-xl font-bold text-orange-600">
                  {orders.filter(o => o.status === 'in_progress').length}
                </div>
                <div className="text-xs text-gray-600">В работе</div>
              </div>
            </Card>
            <Card className="p-2">
              <div className="text-center">
                <div className="text-xl font-bold text-green-600">
                  {orders.filter(o => o.status === 'ready').length}
                </div>
                <div className="text-xs text-gray-600">К доставке</div>
              </div>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Заказы</CardTitle>
                  <CardDescription>Управление заказами на перетяжку мебели</CardDescription>
                </div>
                {user?.role === 'admin' && (
                  <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                    <DialogTrigger asChild>
                      <Button>Создать заказ</Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-md">
                      <DialogHeader>
                        <DialogTitle>Создать новый заказ</DialogTitle>
                        <DialogDescription>
                          Введите информацию о заказчике
                        </DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleCreateOrder} className="space-y-4">
                        <div>
                          <Label htmlFor="customer_name">Имя заказчика</Label>
                          <Input
                            id="customer_name"
                            value={formData.customer_name}
                            onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="customer_phone">Телефон</Label>
                          <Input
                            id="customer_phone"
                            value={formData.customer_phone}
                            onChange={(e) => setFormData({...formData, customer_phone: e.target.value})}
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="customer_address">Адрес</Label>
                          <Textarea
                            id="customer_address"
                            value={formData.customer_address}
                            onChange={(e) => setFormData({...formData, customer_address: e.target.value})}
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="phone_agreement_notes">Заметки о договоренности</Label>
                          <Textarea
                            id="phone_agreement_notes"
                            value={formData.phone_agreement_notes}
                            onChange={(e) => setFormData({...formData, phone_agreement_notes: e.target.value})}
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button type="submit">Создать</Button>
                          <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                            Отмена
                          </Button>
                        </div>
                      </form>
                    </DialogContent>
                  </Dialog>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {orders.map((order) => (
                  <Card key={order.id} className="p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-semibold">
                          Заказ #{order.order_number || order.id}
                        </h4>
                        <p className="text-sm text-gray-600">{order.customer_name}</p>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className={`px-2 py-1 rounded-full text-xs ${statusColors[order.status]}`}>
                          {statusLabels[order.status]}
                        </span>
                        {user?.role === 'admin' && order.price && (
                          <div className="text-lg font-semibold text-green-600 mt-1">
                            {order.price} руб.
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-sm mb-3 space-y-1">
                      {user?.role !== 'work' && order.customer_phone && (
                        <div><strong>📞</strong> {order.customer_phone}</div>
                      )}
                      {order.deadline && (
                        <div><strong>⏰</strong> {new Date(order.deadline).toLocaleDateString('ru-RU')}</div>
                      )}
                      {user?.role !== 'work' && order.customer_address && (
                        <div className="text-gray-600 text-xs"><strong>📍</strong> {order.customer_address}</div>
                      )}
                      <div className="text-gray-500 text-xs"><strong>📅</strong> {new Date(order.created_at).toLocaleDateString('ru-RU')}</div>
                    </div>

                    <div className="flex gap-2 flex-wrap">
                      <Button size="sm" variant="outline" onClick={() => handleViewOrder(order)}>
                        Просмотр
                      </Button>
                      {user?.role === 'admin' && (
                        <Button size="sm" onClick={() => openEditDialog(order)}>
                          Редактировать
                        </Button>
                      )}
                      {user?.role === 'admin' && order.status === 'draft' && (
                        <Button size="sm" onClick={() => handleAction(order.id, 'submit')}>
                          На подтверждение
                        </Button>
                      )}
                      {user?.role === 'admin' && order.status === 'pending_confirmation' && (
                        <Button size="sm" onClick={() => handleAction(order.id, 'confirm')}>
                          Подтвердить
                        </Button>
                      )}
                      {user?.role === 'logist' && order.status === 'confirmed' && (
                        <Button size="sm" onClick={() => openDetailsDialog(order)}>
                          Добавить детали
                        </Button>
                      )}
                      {user?.role === 'work' && order.status === 'in_progress' && (
                        <Button size="sm" onClick={() => handleAction(order.id, 'complete')}>
                          Готово
                        </Button>
                      )}
                      {user?.role === 'logist' && order.status === 'ready' && (
                        <Button size="sm" onClick={() => handleAction(order.id, 'deliver')}>
                          Доставлено
                        </Button>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Order Details Dialog */}
          {selectedOrder && (
            <Dialog open={!!selectedOrder} onOpenChange={() => setSelectedOrder(null)}>
              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Заказ #{selectedOrder.order_number || selectedOrder.id}</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold">Информация о заказе</h3>
                    <p><strong>Имя заказчика:</strong> {selectedOrder.customer_name}</p>
                    {user?.role !== 'work' && (
                      <>
                        <p><strong>Телефон:</strong> {selectedOrder.customer_phone}</p>
                        <p><strong>Адрес:</strong> {selectedOrder.customer_address}</p>
                        {selectedOrder.phone_agreement_notes && (
                          <p><strong>Заметки:</strong> {selectedOrder.phone_agreement_notes}</p>
                        )}
                      </>
                    )}
                    {user?.role === 'admin' && selectedOrder.price && (
                      <p><strong>Цена:</strong> {selectedOrder.price} руб.</p>
                    )}
                    {selectedOrder.customer_requirements && (
                      <p><strong>Требования:</strong> {selectedOrder.customer_requirements}</p>
                    )}
                    {selectedOrder.deadline && user?.role !== 'work' && (
                      <p><strong>Срок:</strong> {new Date(selectedOrder.deadline).toLocaleDateString('ru-RU')}</p>
                    )}
                    {selectedOrder.deadline && user?.role === 'work' && (
                      <p><strong>Дедлайн:</strong> {new Date(selectedOrder.deadline).toLocaleDateString('ru-RU')}</p>
                    )}
                    <p><strong>Статус:</strong> {statusLabels[selectedOrder.status]}</p>
                    <p><strong>Создан:</strong> {new Date(selectedOrder.created_at).toLocaleString('ru-RU')}</p>
                  </div>

                  {(selectedOrder.material_photo || selectedOrder.furniture_photo) && (
                    <div>
                      <h3 className="font-semibold">Фотографии</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {selectedOrder.material_photo && (
                          <div>
                            <p className="text-sm font-medium">Материал</p>
                            <img
                              src={getUploadUrl(selectedOrder.material_photo)}
                              alt="Материал"
                              className="w-full h-32 object-cover rounded"
                              onError={(e) => {
                                // Fallback: try without encoding if encoded version fails
                                const target = e.target as HTMLImageElement;
                                const baseUrl = process.env.NEXT_PUBLIC_API_SERVER_URL || 'http://localhost:8000';
                                const fallbackUrl = `${baseUrl}/uploads/${selectedOrder.material_photo}`;
                                if (target.src !== fallbackUrl) {
                                  target.src = fallbackUrl;
                                }
                              }}
                            />
                          </div>
                        )}
                        {selectedOrder.furniture_photo && (
                          <div>
                            <p className="text-sm font-medium">Мебель</p>
                            <img
                              src={getUploadUrl(selectedOrder.furniture_photo)}
                              alt="Мебель"
                              className="w-full h-32 object-cover rounded"
                              onError={(e) => {
                                // Fallback: try without encoding if encoded version fails
                                const target = e.target as HTMLImageElement;
                                const baseUrl = process.env.NEXT_PUBLIC_API_SERVER_URL || 'http://localhost:8000';
                                const fallbackUrl = `${baseUrl}/uploads/${selectedOrder.furniture_photo}`;
                                if (target.src !== fallbackUrl) {
                                  target.src = fallbackUrl;
                                }
                              }}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {user?.role === 'admin' && (
                    <div>
                      <h3 className="font-semibold">История изменений</h3>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {orderHistory.map((entry, index) => (
                          <div key={index} className="text-sm border-l-2 border-gray-200 pl-4">
                            <p><strong>{entry.user}</strong> - {entry.action}</p>
                            <p className="text-gray-500">{new Date(entry.timestamp).toLocaleString('ru-RU')}</p>
                            {entry.field_changes && (
                              <pre className="text-xs bg-gray-50 p-2 rounded mt-1">
                                {JSON.stringify(entry.field_changes, null, 2)}
                              </pre>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          )}

          {/* Edit Order Dialog */}
          <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Редактировать заказ</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleUpdateOrder} className="space-y-4">
                <div>
                  <Label htmlFor="edit_customer_name">Имя заказчика</Label>
                  <Input
                    id="edit_customer_name"
                    value={formData.customer_name}
                    onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="edit_customer_phone">Телефон</Label>
                  <Input
                    id="edit_customer_phone"
                    value={formData.customer_phone}
                    onChange={(e) => setFormData({...formData, customer_phone: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="edit_customer_address">Адрес</Label>
                  <Textarea
                    id="edit_customer_address"
                    value={formData.customer_address}
                    onChange={(e) => setFormData({...formData, customer_address: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="edit_phone_agreement_notes">Заметки о договоренности</Label>
                  <Textarea
                    id="edit_phone_agreement_notes"
                    value={formData.phone_agreement_notes}
                    onChange={(e) => setFormData({...formData, phone_agreement_notes: e.target.value})}
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit">Сохранить</Button>
                  <Button type="button" variant="outline" onClick={() => setShowEditDialog(false)}>
                    Отмена
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>

          {/* Add Details Dialog */}
          <Dialog open={showDetailsDialog} onOpenChange={setShowDetailsDialog}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Добавить детали заказа</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleAddDetails} className="space-y-4">
                <div>
                  <Label htmlFor="customer_requirements">Требования клиента</Label>
                  <Textarea
                    id="customer_requirements"
                    value={formData.customer_requirements}
                    onChange={(e) => setFormData({...formData, customer_requirements: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="deadline">Срок выполнения</Label>
                  <div className="flex gap-2">
                    <Input
                      id="deadline"
                      type="datetime-local"
                      value={formData.deadline ? (() => {
                        try {
                          const date = new Date(formData.deadline);
                          if (isNaN(date.getTime())) return '';
                          // Format as datetime-local (YYYY-MM-DDTHH:mm)
                          const year = date.getFullYear();
                          const month = String(date.getMonth() + 1).padStart(2, '0');
                          const day = String(date.getDate()).padStart(2, '0');
                          const hours = String(date.getHours()).padStart(2, '0');
                          const minutes = String(date.getMinutes()).padStart(2, '0');
                          return `${year}-${month}-${day}T${hours}:${minutes}`;
                        } catch {
                          return formData.deadline.split('T')[0] || '';
                        }
                      })() : ''}
                      onChange={(e) => {
                        const value = e.target.value;
                        if (value) {
                          // Convert datetime-local to ISO string
                          const date = new Date(value);
                          setFormData({...formData, deadline: date.toISOString()});
                        } else {
                          setFormData({...formData, deadline: ''});
                        }
                      }}
                      required
                      min={new Date().toISOString().slice(0, 16)}
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="price">Цена (руб.)</Label>
                  <Input
                    id="price"
                    type="number"
                    value={formData.price}
                    onChange={(e) => setFormData({...formData, price: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="material_photo">Фото материала</Label>
                  <Input
                    id="material_photo"
                    type="file"
                    accept="image/*"
                    onChange={(e) => setFormData({...formData, material_photo: e.target.files?.[0] || null})}
                  />
                </div>
                <div>
                  <Label htmlFor="furniture_photo">Фото мебели</Label>
                  <Input
                    id="furniture_photo"
                    type="file"
                    accept="image/*"
                    onChange={(e) => setFormData({...formData, furniture_photo: e.target.files?.[0] || null})}
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit">Добавить</Button>
                  <Button type="button" variant="outline" onClick={() => setShowDetailsDialog(false)}>
                    Отмена
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </ProtectedRoute>
  );
}