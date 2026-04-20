package com.portfolio.controller;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.portfolio.entity.Stock;
import com.portfolio.service.StockService;

// @RestController = this class is a REST API controller
// Spring Boot will automatically convert return values to JSON
@RestController

// @RequestMapping = all endpoints in this class start with /api/stocks
// e.g. GET /api/stocks, POST /api/stocks, DELETE /api/stocks/1
@RequestMapping("/api/stocks") 
public class StockController {

    private final StockService service;

    public StockController(StockService service) {
        this.service = service;
    }
    // GET /api/stocks → returns all stocks from the database
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
