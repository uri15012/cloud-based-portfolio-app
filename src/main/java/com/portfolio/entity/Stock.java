package com.portfolio.entity;

import java.math.BigDecimal;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity //SpringBoot already knows how to handle this
@Table(name = "stocks")
public class Stock {
    // those are the fields of Mysql database table
    @Id // the primary key: number that identify each row in the table 
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    //nullable = false means this field is required. You can't add a stock without a symbol. If you try, the database will reject it.
    @Column(nullable = false, length = 10)
    private String symbol;

    @Column(nullable = false)
    private Integer quantity;

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal buyPrice;

    public Stock() {}

    public Stock(String symbol, Integer quantity, BigDecimal buyPrice) {
        this.symbol = symbol;
        this.quantity = quantity;
        this.buyPrice = buyPrice;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }

    public Integer getQuantity() { return quantity; }
    public void setQuantity(Integer quantity) { this.quantity = quantity; }

    public BigDecimal getBuyPrice() { return buyPrice; }
    public void setBuyPrice(BigDecimal buyPrice) { this.buyPrice = buyPrice; }
}
