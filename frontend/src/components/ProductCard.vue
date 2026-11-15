<script setup lang="ts">
import { ArrowUpRight, Plus, PackageOpen } from 'lucide-vue-next'
import type { Product } from '../api/catalog'
import { productArt } from '../utils/product-art'
defineProps<{ product: Product; busy?: boolean }>()
defineEmits<{ add: [product: Product] }>()
</script>
<template>
  <article class="product-card">
    <RouterLink
      :to="'/products/' + product.id"
      class="product-photo"
      :aria-label="'查看' + product.name"
    >
      <img
        v-if="productArt(product.name)"
        :src="productArt(product.name)"
        :alt="product.name + '外观示意'"
        loading="lazy"
      />
      <PackageOpen
        v-else
        class="product-placeholder"
        :size="72"
        :stroke-width="1"
        aria-hidden="true"
      />
      <span v-if="!product.available" class="product-unavailable">暂时缺货</span>
    </RouterLink>
    <div class="product-caption">
      <span>{{ product.category_name }}</span><span>{{ product.available }} 件可售</span>
    </div>
    <RouterLink :to="'/products/' + product.id" class="product-name"
      >{{ product.name }}<ArrowUpRight :size="17" aria-hidden="true"
    /></RouterLink>
    <div class="product-bottom">
      <span class="product-price"><small>¥</small>{{ product.price }}</span
      ><button
        type="button"
        class="product-add"
        :disabled="!product.available || busy"
        :aria-label="'加入购物车：' + product.name"
        @click="$emit('add', product)"
      >
        <Plus :size="16" aria-hidden="true" /><span>{{ busy ? '正在添加' : '加入购物车' }}</span>
      </button>
    </div>
  </article>
</template>
