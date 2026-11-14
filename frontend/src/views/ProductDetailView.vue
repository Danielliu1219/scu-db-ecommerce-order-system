<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { product, type Product } from '../api/catalog'
import { add } from '../api/cart'
const route = useRoute(),
  item = ref<Product>(),
  quantity = ref(1),
  error = ref('')
onMounted(async () => {
  try {
    item.value = await product(String(route.params.id))
  } catch (e) {
    error.value = (e as Error).message
  }
})
async function buy() {
  if (!item.value) return
  try {
    await add(item.value.id, quantity.value)
    ElMessage.success('已加入购物车')
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
</script>
<template>
  <RouterLink to="/products">← 商品列表</RouterLink>
  <p v-if="error" class="error-text">{{ error }}</p>
  <section v-if="item" class="panel" style="margin-top: 24px">
    <p class="muted">{{ item.category_name }}</p>
    <h1>{{ item.name }}</h1>
    <h2 class="money">¥{{ item.price }}</h2>
    <p style="white-space: pre-wrap; line-height: 1.8">{{ item.description || '暂无商品介绍' }}</p>
    <p class="muted">可售库存 {{ item.available }} 件</p>
    <div class="actions">
      <el-input-number
        v-model="quantity"
        :min="1"
        :max="Math.max(1, item.available)"
        :precision="0"
      /><el-button type="primary" :disabled="!item.available" @click="buy">加入购物车</el-button>
    </div>
  </section>
</template>
