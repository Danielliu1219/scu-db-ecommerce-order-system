import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'
import { appBase, demoMode } from '../utils/runtime'
import { useAuth } from '../stores/auth'
import UserLayout from '../layouts/UserLayout.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
const router = createRouter({
  history: demoMode ? createWebHashHistory(appBase) : createWebHistory(appBase),
  routes: [
    { path: '/login', component: () => import('../views/LoginView.vue') },
    { path: '/register', component: () => import('../views/RegisterView.vue') },
    {
      path: '/',
      component: UserLayout,
      meta: { role: 'USER' },
      children: [
        { path: '', redirect: '/products' },
        { path: 'profile', component: () => import('../views/ProfileView.vue') },
        {
          path: 'products',
          component: () => import('../views/ProductListView.vue'),
          meta: { public: true },
        },
        {
          path: 'products/:id',
          component: () => import('../views/ProductDetailView.vue'),
          meta: { public: true },
        },
        { path: 'cart', component: () => import('../views/CartView.vue'), meta: { public: true } },
        { path: 'checkout', component: () => import('../views/CheckoutView.vue') },
        { path: 'orders', component: () => import('../views/OrderListView.vue') },
        { path: 'orders/:id', component: () => import('../views/OrderDetailView.vue') },
      ],
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { role: 'ADMIN' },
      children: [
        { path: '', redirect: '/admin/catalog' },
        { path: 'users', component: () => import('../views/admin/UsersView.vue') },
        { path: 'catalog', component: () => import('../views/admin/CatalogView.vue') },
        { path: 'inventory', component: () => import('../views/admin/InventoryView.vue') },
        { path: 'orders', component: () => import('../views/admin/OrdersView.vue') },
        { path: 'orders/:id', component: () => import('../views/admin/OrderDetailView.vue') },
        { path: 'payments', component: () => import('../views/admin/PaymentsView.vue') },
        { path: 'statistics', component: () => import('../views/admin/StatisticsView.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/products' },
  ],
})
router.beforeEach(async (to) => {
  const auth = useAuth()
  if (to.meta.public) {
    if (!auth.user && sessionStorage.getItem('access_token')) await auth.restore()
    if (auth.user?.role === 'ADMIN') return '/admin/catalog'
    return true
  }
  if (!to.meta.role) return true
  if (!auth.user && !(await auth.restore())) return { path: '/login', query: { next: to.fullPath } }
  if (auth.user?.role !== to.meta.role)
    return auth.user?.role === 'ADMIN' ? '/admin/users' : '/profile'
  return true
})
export default router
