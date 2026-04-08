# LightRAG 知识图谱增量更新与消歧合并原理分析

## 目录
- [1. 概述](#1-概述)
- [2. 核心架构](#2-核心架构)
- [3. 图谱增量更新流程](#3-图谱增量更新流程)
- [4. 实体消歧与合并机制](#4-实体消歧与合并机制)
- [5. 关系消歧与合并机制](#5-关系消歧与合并机制)
- [6. 关键数据结构](#6-关键数据结构)
- [7. 并发控制与数据一致性](#7-并发控制与数据一致性)
- [8. 性能优化策略](#8-性能优化策略)

---

## 1. 概述

LightRAG 是一个高效的检索增强生成系统，其核心特性之一是支持知识图谱的**增量更新**和**智能消歧合并**。本文档详细解析其内部实现原理。

### 1.1 核心特性

- **增量更新**: 支持文档级别的增量知识注入，无需重建整个图谱
- **智能消歧**: 自动识别和合并来自不同 chunk 的相同实体/关系
- **并行处理**: 使用异步并发技术提升处理效率
- **多级存储**: Graph + VDB + KV 三层存储架构
- **版本控制**: 基于时间戳和 source_id 的版本追踪

---

## 2. 核心架构

### 2.1 三层存储架构

```
┌─────────────────────────────────────┐
│   应用层 (LightRAG Class)           │
│   - insert()                        │
│   - merge_nodes_and_edges()         │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   操作层 (operate.py)               │
│   - extract_entities()              │
│   - _merge_nodes_then_upsert()      │
│   - _merge_edges_then_upsert()      │
│   - rebuild_knowledge_from_chunks() │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   存储层 (kg/*.py)                  │
│   - BaseGraphStorage (NetworkX)     │
│   - BaseVectorStorage (NanoVectorDB)│
│   - BaseKVStorage (JSON)            │
└─────────────────────────────────────┘
```

### 2.2 核心组件

#### 2.2.1 图谱存储 (Graph Storage)
- **实现**: `NetworkXStorage` (基于 NetworkX 图数据库)
- **功能**: 存储实体节点和关系边
- **特性**: 
  - 无向图设计
  - 支持节点/边的增删改查
  - 基于 GraphML 文件持久化

#### 2.2.2 向量存储 (Vector Storage)
- **实现**: `BaseVectorStorage` (如 NanoVectorDB)
- **功能**: 存储实体/关系/文本块的向量嵌入
- **用途**: 语义相似度搜索

#### 2.2.3 键值存储 (KV Storage)
- **实现**: `BaseKVStorage` (如 JsonKVStorage)
- **功能**: 
  - 存储完整文档 (`full_docs`)
  - 存储文本块 (`text_chunks`)
  - 存储 LLM 响应缓存 (`llm_response_cache`)
  - 存储文档级实体/关系索引 (`full_entities`, `full_relations`)
  - 追踪实体/关系的完整 chunk 列表 (`entity_chunks`, `relation_chunks`)

---

## 3. 图谱增量更新流程

### 3.1 整体流程

```python
insert(document) 
  ↓
[Step 1] 文档分块 (chunking_by_token_size)
  ↓
[Step 2] 实体关系抽取 (extract_entities)
  ├─ 并行处理每个 chunk
  ├─ LLM 提取 (带 gleaning 增强)
  └─ 缓存 extraction results
  ↓
[Step 3] 合并与消歧 (merge_nodes_and_edges)
  ├─ Phase 1: 合并所有实体
  ├─ Phase 2: 合并所有关系
  └─ Phase 3: 更新文档索引
  ↓
[Step 4] 持久化 (index_done_callback)
```

### 3.2 详细步骤

#### Step 1: 文档分块
```python
chunks = chunking_by_token_size(
    tokenizer=tokenizer,
    content=document_text,
    chunk_token_size=1200,  # 默认值
    chunk_overlap_token_size=100  # 重叠区域保持上下文
)
```

**关键点**:
- 按 token 数切分（非字符数）
- chunk 间保留重叠区域防止信息丢失
- 每个 chunk 分配唯一 ID: `chunk-{md5hash}`

#### Step 2: 实体关系抽取

```python
async def extract_entities(chunks, global_config):
    # 并行处理所有 chunk
    tasks = [_process_single_content(chunk) for chunk in chunks]
    chunk_results = await asyncio.gather(*tasks)
    return chunk_results
```

**单 chunk 处理流程**:
```python
async def _process_single_content(chunk_key_dp):
    # 1. 初始提取
    final_result = await use_llm_func_with_cache(
        entity_extraction_user_prompt,
        cache_type="extract",
        chunk_id=chunk_key
    )
    
    # 2. Gleaning 增强 (可选，最多 entity_extract_max_gleaning 次)
    if entity_extract_max_gleaning > 0:
        glean_result = await use_llm_func_with_cache(
            entity_continue_extraction_user_prompt,
            history_messages=history
        )
        # 比较描述长度，保留更好的版本
        maybe_nodes = merge_gleaning_results(maybe_nodes, glean_nodes)
    
    # 3. 解析 LLM 输出
    maybe_nodes, maybe_edges = await _process_extraction_result(
        final_result,
        chunk_key,
        timestamp,
        file_path
    )
    
    return maybe_nodes, maybe_edges
```

**LLM 输出格式**:
```
实体：
("<|entity|>", "实体名", "实体类型", "描述<|COMPLETE|>")

关系：
("<|relationship|>", "源实体", "目标实体", "关键词", "描述", 权重<|COMPLETE|>")
```

#### Step 3: 合并与消歧

这是最核心的步骤，详见第 4、5 节。

#### Step 4: 持久化

```python
async def index_done_callback():
    # 1. 保存 Graph 到 GraphML 文件
    NetworkXStorage.write_nx_graph(graph, graphml_file)
    
    # 2. 保存 VDB 数据
    vector_db_storage.persist()
    
    # 3. 保存 KV 数据
    kv_storage.persist()
    
    # 4. 设置更新标志通知其他进程
    set_all_update_flags(namespace, workspace)
```

---

## 4. 实体消歧与合并机制

### 4.1 消歧策略

**核心原则**: 相同 entity_name 的实体会被自动合并

```python
async def _merge_nodes_then_upsert(entity_name, entities_data, ...):
    """
    合并同一实体的多个提取结果
    
    Args:
        entity_name: 实体名称 (消歧的关键标识)
        entities_data: 来自不同 chunk 的该实体提取结果列表
    """
```

### 4.2 合并流程

```python
# 1. 获取已存在的实体数据
already_node = await knowledge_graph_inst.get_node(entity_name)
if already_node:
    already_source_ids = already_node["source_id"].split(GRAPH_FIELD_SEP)
    already_description = already_node["description"].split(GRAPH_FIELD_SEP)
    already_entity_types = [already_node["entity_type"]]
    already_file_paths = already_node["file_path"].split(GRAPH_FIELD_SEP)

# 2. 从 entity_chunks storage 获取完整的 chunk IDs
existing_full_source_ids = []
if entity_chunks_storage:
    stored_chunks = await entity_chunks_storage.get_by_id(entity_name)
    existing_full_source_ids = stored_chunks["chunk_ids"]

# 3. 合并新的 source_ids
new_source_ids = [dp["source_id"] for dp in nodes_data]
full_source_ids = merge_source_ids(existing_full_source_ids, new_source_ids)

# 4. 应用 source_id 限制策略 (KEEP 或 FIFO)
limit_method = global_config.get("source_ids_limit_method")
max_source_limit = global_config.get("max_source_ids_per_entity")
source_ids = apply_source_ids_limit(
    full_source_ids,
    max_source_limit,
    limit_method
)

# 5. 去重：按 description 去重，保留同一文档中首次出现的
unique_nodes = {}
for dp in nodes_data:
    desc = dp.get("description")
    if desc not in unique_nodes:
        unique_nodes[desc] = dp

# 6. 排序：按时间戳 + 描述长度排序
sorted_nodes = sorted(
    unique_nodes.values(),
    key=lambda x: (x.get("timestamp", 0), -len(x.get("description", "")))
)

# 7. 合并描述列表
description_list = already_description + [dp["description"] for dp in sorted_nodes]

# 8. LLM 摘要 (Map-Reduce 策略)
description, llm_was_used = await _handle_entity_relation_summary(
    "Entity",
    entity_name,
    description_list,
    GRAPH_FIELD_SEP,
    global_config
)

# 9. 确定最终 entity_type (投票机制)
entity_type = Counter(
    [dp["entity_type"] for dp in nodes_data] + already_entity_types
).most_common(1)[0][0]

# 10. 构建 file_path (带数量限制)
file_path = build_file_path_with_limit(
    already_file_paths + [dp.get("file_path") for dp in nodes_data],
    max_file_paths
)

# 11. 更新 Graph 和 VDB
await knowledge_graph_inst.upsert_node(entity_name, node_data={
    "entity_id": entity_name,
    "entity_type": entity_type,
    "description": description,
    "source_id": GRAPH_FIELD_SEP.join(source_ids),
    "file_path": file_path,
    "created_at": int(time.time()),
    "truncate": truncation_info
})
```

### 4.3 关键机制详解

#### 4.3.1 Source ID 管理

**问题**: 如何追踪实体来自哪些 chunk？

**解决方案**:
- 每个实体维护一个 `source_id` 列表
- `source_id` = chunk IDs 的拼接（用 `GRAPH_FIELD_SEP` 分隔）
- 使用 `entity_chunks_storage` 存储完整的 chunk 列表（不受限制）
- Graph 和 VDB 中的 `source_id` 受 `max_source_ids_per_entity` 限制

**限制策略**:
```python
# KEEP 策略：保留最早的 chunk
if limit_method == SOURCE_IDS_LIMIT_METHOD_KEEP:
    truncated = source_ids[:max_source_limit]
    
# FIFO 策略：保留最新的 chunk
elif limit_method == SOURCE_IDS_LIMIT_METHOD_FIFO:
    truncated = source_ids[-max_source_limit:]
```

#### 4.3.2 描述去重与合并

**问题**: 同一实体在不同 chunk 中可能有相似描述

**解决方案**:
1. **去重**: 以 description 为 key，保留首次出现
2. **排序**: 按时间戳升序，同时间戳按描述长度降序
3. **合并**: 使用 LLM 进行 Map-Reduce 摘要

**示例**:
```python
# 原始描述列表
descriptions = [
    "苹果公司是一家科技公司",  # chunk-1
    "苹果是全球最有价值的品牌",  # chunk-2
    "苹果公司是一家科技公司",  # chunk-3 (重复，会被过滤)
    "苹果总部位于加州",  # chunk-4
]

# 去重后
unique_descriptions = [
    "苹果公司是一家科技公司",  # 保留 chunk-1 的
    "苹果是全球最有价值的品牌",
    "苹果总部位于加州",
]

# LLM 摘要后
final_description = "苹果公司是一家全球最有价值的科技公司，总部位于加州"
```

#### 4.3.3 Entity Type 投票

**问题**: 同一实体在不同 chunk 中可能被标注为不同类型

**解决方案**: 多数投票
```python
entity_types = ["公司", "组织", "公司", "品牌", "公司"]
final_entity_type = Counter(entity_types).most_common(1)[0][0]  # "公司"
```

---

## 5. 关系消歧与合并机制

### 5.1 关系标识

**关键设计**: 关系由 `(src_id, tgt_id)` 唯一标识
```python
# 关系 key 的计算 (确保无向图的一致性)
sorted_edge_key = tuple(sorted(edge_key))  # ("苹果", "iPhone")
```

### 5.2 合并流程

```python
async def _merge_edges_then_upsert(src_id, tgt_id, edges_data, ...):
    """
    合并同一关系的多个提取结果
    
    Args:
        src_id: 源实体名
        tgt_id: 目标实体名
        edges_data: 来自不同 chunk 的该关系提取结果列表
    """

# 1. 获取已存在的关系数据
already_edge = await knowledge_graph_inst.get_edge(src_id, tgt_id)
if already_edge:
    already_weights = [already_edge.get("weight", 1.0)]
    already_source_ids = already_edge["source_id"].split(GRAPH_FIELD_SEP)
    already_description = already_edge["description"].split(GRAPH_FIELD_SEP)
    already_keywords = split_string_by_multi_markers(already_edge["keywords"])
    already_file_paths = already_edge["file_path"].split(GRAPH_FIELD_SEP)

# 2. 从 relation_chunks storage 获取完整 chunk IDs
storage_key = make_relation_chunk_key(src_id, tgt_id)
existing_full_source_ids = []
if relation_chunks_storage:
    stored_chunks = await relation_chunks_storage.get_by_id(storage_key)
    existing_full_source_ids = stored_chunks["chunk_ids"]

# 3. 合并新的 source_ids
new_source_ids = [dp["source_id"] for dp in edges_data]
full_source_ids = merge_source_ids(existing_full_source_ids, new_source_ids)

# 4. 应用 source_id 限制策略
source_ids = apply_source_ids_limit(
    full_source_ids,
    global_config["max_source_ids_per_relation"],
    limit_method
)

# 5. 去重：按 description 去重
unique_edges = {}
for dp in edges_data:
    desc = dp.get("description")
    if desc not in unique_edges:
        unique_edges[desc] = dp

# 6. 排序：按时间戳 + 描述长度
sorted_edges = sorted(
    unique_edges.values(),
    key=lambda x: (x.get("timestamp", 0), -len(x.get("description", "")))
)

# 7. 合并描述列表
description_list = already_description + [dp["description"] for dp in sorted_edges]

# 8. LLM 摘要
description, llm_was_used = await _handle_entity_relation_summary(
    "Relation",
    f"({src_id}, {tgt_id})",
    description_list,
    GRAPH_FIELD_SEP,
    global_config
)

# 9. 合并 keywords (去重后拼接)
all_keywords = set()
for keyword_str in already_keywords + [dp.get("keywords") for dp in edges_data]:
    all_keywords.update(k.strip() for k in keyword_str.split(",") if k.strip())
keywords = ",".join(sorted(all_keywords))

# 10. 累加 weight
weight = sum([dp["weight"] for dp in edges_data] + already_weights)

# 11. 构建 file_path (带数量限制)
file_path = build_file_path_with_limit(
    already_file_paths + [dp.get("file_path") for dp in edges_data],
    max_file_paths
)

# 12. 更新 Graph 和 VDB
await knowledge_graph_inst.upsert_edge(src_id, tgt_id, edge_data={
    "weight": weight,
    "description": description,
    "keywords": keywords,
    "source_id": GRAPH_FIELD_SEP.join(source_ids),
    "file_path": file_path,
    "created_at": int(time.time()),
    "truncate": truncation_info
})
```

### 5.3 关键机制详解

#### 5.3.1 Weight 累加机制

**设计思想**: 关系被提及的次数越多，weight 越高

```python
# 每次插入新关系时 weight=1.0
# 合并时累加所有 weight
weight = sum(new_weights) + sum(existing_weights)

# 示例:
# chunk-1: 苹果 -> iPhone (weight=1.0)
# chunk-2: 苹果 -> iPhone (weight=1.0)
# 合并后：weight=2.0 (表示该关系被提及 2 次)
```

#### 5.3.2 Keywords 合并

**策略**: 并集合并，去重后按字母排序
```python
# 原始 keywords
keywords_list = ["智能手机，电子产品", "高端，智能手机", "创新"]

# 拆分并去重
all_keywords = {"智能手机", "电子产品", "高端", "创新"}

# 合并结果
keywords = "创新，高端，电子产品，智能手机"
```

---

## 6. 关键数据结构

### 6.1 实体节点结构

```python
node_data = {
    "entity_id": str,          # 实体名称 (唯一标识)
    "entity_type": str,        # 实体类型
    "description": str,        # 合并后的描述
    "source_id": str,          # chunk IDs 拼接 (受限)
    "file_path": str,          # 文件路径拼接 (受限)
    "created_at": int,         # 创建时间戳
    "truncate": str            # 截断信息
}
```

### 6.2 关系边结构

```python
edge_data = {
    "src_id": str,             # 源实体
    "tgt_id": str,             # 目标实体
    "weight": float,           # 权重 (累加值)
    "description": str,        # 合并后的描述
    "keywords": str,           # 关键词拼接
    "source_id": str,          # chunk IDs 拼接 (受限)
    "file_path": str,          # 文件路径拼接 (受限)
    "created_at": int,         # 创建时间戳
    "truncate": str            # 截断信息
}
```

### 6.3 Chunk 追踪结构

```python
# entity_chunks storage
{
    "entity_name": {
        "chunk_ids": ["chunk-1", "chunk-2", "chunk-3"],  # 完整列表
        "count": 3
    }
}

# relation_chunks storage
{
    "src_id<SEP>tgt_id": {
        "chunk_ids": ["chunk-1", "chunk-2"],  # 完整列表
        "count": 2
    }
}
```

---

## 7. 并发控制与数据一致性

### 7.1 三级锁机制

```python
# Level 1: 全局锁 (namespace 级别)
async with get_namespace_lock(namespace, workspace):
    # Level 2: Storage keyed 锁 (entity/relation 级别)
    async with get_storage_keyed_lock([entity_name], namespace):
        # Level 3: Pipeline status 锁
        async with pipeline_status_lock:
            # 执行实际操作
```

### 7.2 两阶段提交

**Phase 1: 内存中更新**
```python
# 在内存中的 NetworkX 图上操作
graph.add_node(node_id, **node_data)
graph.add_edge(src_id, tgt_id, **edge_data)
```

**Phase 2: 持久化到磁盘**
```python
async def index_done_callback():
    # 一次性写入所有变更
    nx.write_graphml(graph, graphml_file)
    vector_db.persist()
    kv_storage.persist()
    
    # 设置更新标志
    storage_updated.value = True
```

### 7.3 跨进程同步

```python
# 进程 A 完成写入后
await set_all_update_flags(namespace, workspace)

# 进程 B 读取前检查
async def _get_graph():
    async with self._storage_lock:
        if self.storage_updated.value:
            # 重新加载数据
            self._graph = NetworkXStorage.load_nx_graph(self._graphml_xml_file)
            self.storage_updated.value = False
```

---

## 8. 性能优化策略

### 8.1 并行处理

```python
# 实体提取阶段：并行处理所有 chunk
chunk_max_async = global_config.get("llm_model_max_async", 4)
semaphore = asyncio.Semaphore(chunk_max_async)
tasks = [process_with_semaphore(chunk) for chunk in chunks]
chunk_results = await asyncio.gather(*tasks)

# 合并阶段：并行处理所有实体/关系
graph_max_async = global_config.get("llm_model_max_async", 4) * 2
semaphore = asyncio.Semaphore(graph_max_async)

# Phase 1: 并行处理实体
entity_tasks = [
    create_task(_locked_process_entity_name(name, entities))
    for name, entities in all_nodes.items()
]

# Phase 2: 并行处理关系
edge_tasks = [
    create_task(_locked_process_edges(key, edges))
    for key, edges in all_edges.items()
]
```

### 8.2 缓存机制

#### LLM 响应缓存
```python
# 使用 compute_args_hash 生成缓存 key
cache_key = compute_args_hash(prompt, model_name, params)

# 检查缓存
cached_result = await handle_cache(hashing_kv, cache_key)
if cached_result:
    return cached_result

# 调用 LLM 并保存结果
result = await llm_func(prompt)
await save_to_cache(hashing_kv, CacheData(
    args_hash=cache_key,
    content=result,
    cache_type="extract"
))
```

#### Embedding 缓存
```python
embedding_cache_config = {
    "enabled": True,
    "similarity_threshold": 0.95,  # 相似度阈值
    "use_llm_check": False  # 是否使用 LLM 验证
}
```

### 8.3 批量操作

```python
# 批量获取节点
nodes = await knowledge_graph_inst.get_nodes_batch(node_ids)

# 批量获取边
edges = await knowledge_graph_inst.get_edges_batch(pairs)

# 批量删除 VDB 记录
await relationships_vdb.delete([rel_vdb_id, rel_vdb_id_reverse])
```

### 8.4 Token 限制策略

```python
# 1. 输入限制
max_extract_input_tokens = 4000
if token_count > max_input_tokens:
    logger.warning("Gleaning stopped: Input tokens exceeded limit")

# 2. 摘要限制
summary_context_size = 2000  # LLM 上下文窗口
summary_max_tokens = 500     # 输出限制

# 3. 查询限制
max_total_tokens = 8000  # 总 token 预算
max_entity_tokens = 2000
max_relation_tokens = 2000
max_chunk_tokens = 4000
```

---

## 总结

LightRAG 的图谱增量更新与消歧合并机制具有以下特点：

### 核心优势
1. **高效增量**: 支持文档级增量更新，无需重建全图
2. **智能消歧**: 基于 entity_name/relation_key 自动识别和合并
3. **版本追踪**: 完善的 source_id 和 chunk 追踪机制
4. **并发安全**: 三级锁机制保证数据一致性
5. **灵活配置**: 可配置的限制策略 (KEEP/FIFO)

### 技术亮点
1. **Map-Reduce 摘要**: 递归合并超长描述列表
2. **Weight 累加**: 关系重要性量化
3. **Type 投票**: 多数投票确定最佳类型
4. **两级存储**: 完整列表 (entity_chunks) + 受限视图 (source_id)

### 适用场景
- 大规模知识库构建
- 多文档知识融合
- 实时更新的知识图谱
- 需要溯源的知识管理系统

---

## 附录：关键代码位置

- **主入口**: `lightrag.py::LightRAG.insert()`
- **实体提取**: `operate.py::extract_entities()`
- **实体合并**: `operate.py::_merge_nodes_then_upsert()`
- **关系合并**: `operate.py::_merge_edges_then_upsert()`
- **图谱存储**: `kg/networkx_impl.py::NetworkXStorage`
- **工具函数**: `utils.py::merge_source_ids()`, `apply_source_ids_limit()`
