<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as api from '../../api/catalog'
import { states } from '../../utils/format'
const categories = ref<api.Category[]>([]),
  rows = ref<api.Product[]>([]),
  total = ref(0),
  filters = reactive({ keyword: '', category_id: '', status: '', page: 1, page_size: 20 })
const dialog = ref(false),
  editing = ref(''),
  busy = ref(false),
  form = reactive({
    category_id: '',
    name: '',
    price: '',
    description: '',
    status: 'OFF_SHELF' as api.Product['status'],
  })
async function load(reset = false) {
  if (reset) filters.page = 1
  try {
    const [c, p] = await Promise.all([api.categories(true), api.products(filters, true)])
    categories.value = c
    rows.value = p.items
    total.value = p.total
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
function open(p?: api.Product) {
  editing.value = p?.id || ''
  Object.assign(
    form,
    p
      ? {
          category_id: p.category_id,
          name: p.name,
          price: p.price,
          description: p.description,
          status: p.status,
        }
      : {
          category_id: categories.value[0]?.id || '',
          name: '',
          price: '',
          description: '',
          status: 'OFF_SHELF',
        },
  )
  dialog.value = true
}
async function save() {
  busy.value = true
  try {
    if (editing.value) {
      const { status, ...body } = form
      await api.editProduct(editing.value, body)
    } else await api.createProduct(form)
    dialog.value = false
    ElMessage.success('商品已保存')
    await load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    busy.value = false
  }
}
async function category(c?: api.Category) {
  try {
    const { value } = await ElMessageBox.prompt('输入单层分类名称', '维护分类', {
      inputValue: c?.name || '',
      inputValidator: (v) => !!v?.trim() || '请输入名称',
    })
    await api.saveCategory(value, c?.id)
    await load()
  } catch (e) {
    if (e instanceof Error) ElMessage.error(e.message)
  }
}
async function removeCategory(c: api.Category) {
  try {
    await ElMessageBox.confirm('确认删除分类“' + c.name + '”？', '删除分类')
    await api.deleteCategory(c.id)
    await load()
  } catch (e) {
    if (e instanceof Error) ElMessage.error(e.message)
  }
}
async function toggle(p: api.Product) {
  try {
    await api.productStatus(p.id, p.status === 'ON_SHELF' ? 'OFF_SHELF' : 'ON_SHELF')
    await load()
  } catch (e) {
    ElMessage.error((e as Error).message)
  }
}
async function remove(p: api.Product) {
  try {
    await ElMessageBox.confirm('仅无业务引用且库存为零的商品可以删除。', '确认删除')
    await api.deleteProduct(p.id)
    await load()
  } catch (e) {
    if (e instanceof Error) ElMessage.error(e.message)
  }
}
onMounted(() => load())
</script>
<template>
  <div class="page-head">
    <div>
      <h1>商品与分类</h1>
      <span class="muted">维护商品资料、销售状态与单层分类</span>
    </div>
    <el-button type="primary" @click="open()">新增商品</el-button>
  </div>
  <section class="panel">
    <div class="page-head">
      <h3>商品分类</h3>
      <el-button @click="category()">新增分类</el-button>
    </div>
    <div class="toolbar">
      <div v-for="c in categories" :key="c.id">
        <el-button @click="category(c)">{{ c.name }}</el-button><el-button
          text
          type="danger"
          @click="removeCategory(c)"
          >删除</el-button
        >
      </div>
      <span v-if="!categories.length" class="muted">请先创建分类</span>
    </div>
  </section>
  <section class="panel">
    <form class="toolbar" @submit.prevent="load(true)">
      <el-input v-model="filters.keyword" placeholder="商品名称" clearable /><el-select
        v-model="filters.category_id"
        placeholder="全部分类"
        clearable
        ><el-option v-for="c in categories" :key="c.id" :value="c.id" :label="c.name" /></el-select
      ><el-select v-model="filters.status" placeholder="全部状态" clearable
        ><el-option value="ON_SHELF" label="上架" /><el-option
          value="OFF_SHELF"
          label="下架" /></el-select
      ><el-button native-type="submit">查询</el-button>
    </form>
    <el-table :data="rows" empty-text="无匹配商品"
      ><el-table-column prop="id" label="编号" width="90" /><el-table-column
        prop="name"
        label="商品名称"
        min-width="160"
      /><el-table-column prop="category_name" label="分类" /><el-table-column label="售价"
        ><template #default="{ row }"
          ><span class="money">¥{{ row.price }}</span></template
        ></el-table-column
      ><el-table-column prop="available" label="可售量" /><el-table-column label="状态"
        ><template #default="{ row }"
          ><el-tag :type="row.status === 'ON_SHELF' ? 'success' : 'info'">{{
            states[row.status]
          }}</el-tag></template
        ></el-table-column
      ><el-table-column label="操作" width="240"
        ><template #default="{ row }"
          ><el-button link @click="open(row)">编辑</el-button
          ><el-button link @click="toggle(row)">{{
            row.status === 'ON_SHELF' ? '下架' : '上架'
          }}</el-button
          ><el-button link type="danger" @click="remove(row)">删除</el-button></template
        ></el-table-column
      ></el-table
    ><el-pagination
      v-model:current-page="filters.page"
      :total="total"
      :page-size="20"
      layout="prev,pager,next,total"
      @current-change="load()"
    />
  </section>
  <el-dialog v-model="dialog" :title="editing ? '编辑商品' : '新增商品'" width="min(600px,94vw)"
    ><el-form label-width="90px" @submit.prevent="save"
      ><el-form-item label="商品名称"><el-input v-model="form.name" maxlength="100" /></el-form-item
      ><el-form-item label="分类"
        ><el-select v-model="form.category_id"
          ><el-option
            v-for="c in categories"
            :key="c.id"
            :value="c.id"
            :label="c.name" /></el-select></el-form-item
      ><el-form-item label="售价（元）"
        ><el-input v-model="form.price" placeholder="例如30.00" /></el-form-item
      ><el-form-item label="介绍"
        ><el-input v-model="form.description" type="textarea" :rows="4" /></el-form-item
      ><el-form-item v-if="!editing" label="初始状态"
        ><el-select v-model="form.status"
          ><el-option value="OFF_SHELF" label="下架" /><el-option
            value="ON_SHELF"
            label="上架" /></el-select></el-form-item
      ><el-button type="primary" native-type="submit" :loading="busy">保存商品</el-button></el-form
    ></el-dialog
  >
</template>
