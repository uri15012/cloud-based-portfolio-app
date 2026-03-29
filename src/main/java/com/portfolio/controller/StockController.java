package com.portfolio.controller;

import com.portfolio.entity.Stock;
import com.portfolio.service.StockService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/stocks")
public class StockController {

    private final StockService service;

    public StockController(StockService service) {
        this.service = service;
    }

    @GetMapping
    public List<Stock> getAll() {
        return service.findAll();
    }

    @GetMapping("/{id}")
    public Stock getById(@PathVariable Long id) {
        return service.findById(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Stock create(@RequestBody Stock stock) {
        return service.create(stock);
    }

    @PutMapping("/{id}")
    public Stock update(@PathVariable Long id, @RequestBody Stock stock) {
        return service.update(id, stock);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        service.delete(id);
    }
}
