-- 迁移脚本: production_batches 增加 current_furnace_id
ALTER TABLE production_batches ADD COLUMN current_furnace_id INT DEFAULT NULL AFTER current_section;
ALTER TABLE production_batches ADD CONSTRAINT fk_batch_current_furnace FOREIGN KEY (current_furnace_id) REFERENCES furnaces(id);

-- 初始化现有数据: 将现有批次指向其所属炉子(通过production_runs关联)
UPDATE production_batches pb
JOIN production_runs pr ON pb.production_run_id = pr.id
SET pb.current_furnace_id = pr.furnace_id
WHERE pb.current_furnace_id IS NULL;
