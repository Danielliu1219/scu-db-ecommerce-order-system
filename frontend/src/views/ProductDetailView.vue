<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, ShoppingBag, PackageOpen, ArrowRight } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import { product, type Product } from '../api/catalog'
import { add } from '../api/cart'
import { productArt } from '../utils/product-art'
import { guestSession } from '../utils/runtime'
const route = useRoute(),
  item = ref<Product>(),
  quantity = ref(1),
  error = ref(''),
  busy = ref(false)
watch(
  () => route.params.id,
  async () => {
    item.value = undefined
    error.value = ''
    try {
      item.value = await product(String(route.params.id))
    } catch (e) {
      error.value = (e as Error).message
    }
  },
  { immediate: true },
)
async function buy() {
  if (!item.value) return
  busy.value = true
  try {
    await add(item.value.id, quantity.value)
    ElMessage.success(guestSession() ? '已加入游客购物车' : '已加入购物车')
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <RouterLink to="/products" class="back-link"><ArrowLeft :size="16" />返回商品目录</RouterLink>
  <div v-if="error" class="inline-error" role="alert">{{ error }}</div>
  <section v-if="item" class="product-detail">
    <div class="detail-photo">
      <img
        v-if="productArt(item.name)"
        :src="productArt(item.name)"
        :alt="item.name + '外观示意'"
      /><PackageOpen v-else :size="120" :stroke-width="1" />
    </div>
    <div class="detail-copy">
      <p class="eyebrow">{{ item.category_name }}</p>
      <h1>{{ item.name }}</h1>
      <p class="detail-price"><small>¥</small>{{ item.price }}</p>
      <p class="detail-description">{{ item.description || '暂无商品介绍。' }}</p>
      <dl class="detail-facts">
        <div>
          <dt>可售库存</dt>
          <dd>{{ item.available }} 件</dd>
        </div>
        <div>
          <dt>商品编号</dt>
          <dd>{{ item.id }}</dd>
        </div>
        <div>
          <dt>结算说明</dt>
          <dd>下单时重新核价与核对库存</dd>
        </div>
      </dl>
      <div class="detail-purchase">
        <el-input-number
          v-model="quantity"
          :min="1"
          :max="Math.max(1, item.available)"
          :precision="0"
          aria-label="购买数量"
        /><el-button type="primary" :disabled="!item.available" :loading="busy" @click="buy"
          ><ShoppingBag :size="17" />{{ item.available ? '加入购物车' : '暂无库存' }}</el-button
        >
      </div>
      <RouterLink to="/cart" class="text-action">查看购物车 <ArrowRight :size="17" /></RouterLink>
      <p v-if="guestSession()" class="detail-note">游客加购不会扣减库存，可在购物车中继续修改。</p>
    </div>
  </section>
  <el-skeleton v-else-if="!error" :rows="8" animated />
</template>
