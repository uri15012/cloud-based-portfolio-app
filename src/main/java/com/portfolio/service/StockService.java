package com.portfolio.service;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import com.portfolio.entity.Stock;
import com.portfolio.repository.StockRepository;

//update, find a stock 
@Service
public class StockService {

    private final StockRepository repository;

    public StockService(StockRepository repository) {
        this.repository = repository;
    }
    
    // in case we want to see all the stocks 
    public List<Stock> findAll() {
        return repository.findAll();
    }

    public Stock findById(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Stock not found with id: " + id));
    }

    public Stock create(Stock stock) {
        return repository.save(stock);
    }

    public Stock update(Long id, Stock updated) {
        Stock existing = findById(id);
        existing.setSymbol(updated.getSymbol());
        existing.setQuantity(updated.getQuantity());
        existing.setBuyPrice(updated.getBuyPrice());
        return repository.save(existing);
    }

    public void delete(Long id) {
        findById(id);
        repository.deleteById(id);
    }
}
